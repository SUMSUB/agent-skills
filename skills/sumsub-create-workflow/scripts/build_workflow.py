#!/usr/bin/env python3
"""
Assemble a workflow spec (JSON on stdin) into a full Sumsub `ApplicantWorkflow`
payload (JSON on stdout).

Spec format: see SKILL.md.

This is a thin assembler + validator, NOT a translator. Nodes use the real
schema node-type names; edge conditions are the real Sumsub AST authored
directly (`{or:[{and:[{op, args:[{exp},{lit}]}]}]}`), where:
  - `{exp: "<raw path>"}`  is an expression path, verbatim (incl. bracket paths).
  - `{lit: "<json>"}`      is a literal, given **already JSON-encoded as a string**
                           the way the API stores it ("USA" → "\"USA\"", 3 → "3",
                           ["A","B"] → "[\"A\", \"B\"]"). The API rejects an
                           un-encoded literal, so the encoding is mandatory.

What the assembler does (and only this):
- Validates node types, operators, action targetType, and `lit` length against
  small built-in known sets, and rejects a top-level `Condition.negate`. (Review
  labels, levels, and client lists are left to the API's authoritative validate.)
- Enforces the edge invariant: only `exclusiveChoice` nodes may branch or gate;
  every other node has at most one unconditional out-edge (no auto-insert — author
  the choice explicitly).
- Graph validation: dangling edges, duplicate ids, missing required fields,
  kind/node-type coherence.
- Convenience: node bodies may be flattened (`levelName`, `labels`, `actions`,
  `buttonIds`, `disableGoBack`) or written in the real nested form; `on:` is a
  shorthand for `reviewDecisions`.
"""
import json
import sys
from collections import Counter, defaultdict

# ---------- known validation sets --------------------------------------------
# Small, stable sets the assembler checks against so typos and unsupported
# constructs fail here — with a precise, enumerated message — before any network
# call. They mirror the API's enums; `POST /-/validate` is authoritative for
# everything else (levels, client lists, review labels, transitions).
KNOWN_NODE_TYPES = {
    "actionActions", "actionApplicantLevel", "actionApplicantTransition",
    "actionExclusiveChoice", "actionFinalRejection", "actionManualReview",
    "actions", "applicantLevel", "exclusiveChoice", "finalRejection", "manualReview",
}
ACTION_PREFIXED_NODE_TYPES = {
    "actionActions", "actionApplicantLevel", "actionApplicantTransition",
    "actionExclusiveChoice", "actionFinalRejection", "actionManualReview",
}
REVIEW_DECISIONS = {"approved", "rejected", "resubmission"}
TARGET_TYPES = {"applicant", "applicantAction"}
OPERATORS = {
    "eq", "eqIgnoreCase", "neIgnoreCase", "eqOrNull", "eqIgnoreCaseOrNull", "ne",
    "lt", "lte", "gt", "gte", "match", "notMatch", "in", "notIn",
    "startsWith", "notStartsWith", "endsWith", "notEndsWith", "empty", "notEmpty",
    "contains", "notContains", "containsAny", "notContainsAny", "containsAll",
    "containsOnly",
}
RESERVED_OPERATORS = {"call"}

# Node-type groups (real schema names). Sumsub rejects mixing standard and action
# node types in one workflow: action-* types only belong in an action workflow
# (kind="actions"); the standard types only in a verification workflow
# (kind="default"|"test").
LEVEL_NODE_TYPES = {"applicantLevel", "actionApplicantLevel"}
ACTIONS_NODE_TYPES = {"actions", "actionActions"}
REJECT_NODE_TYPES = {"finalRejection", "actionFinalRejection"}
REVIEW_NODE_TYPES = {"manualReview", "actionManualReview"}
CHOICE_NODE_TYPES = {"exclusiveChoice", "actionExclusiveChoice"}
TRANSITION_NODE_TYPES = {"actionApplicantTransition"}


def _list(v):
    return v if isinstance(v, list) else [v]


# ---------- action item builders ----------------------------------------------
# Author-supported actions: tags / notes / sourceKey. (kytCase is postponed — no
# public API for blueprintId yet; riskScore/recheck are not supported.)

def _build_tags_action(v) -> dict:
    """`{tag: [...]}` (add) or `{tag: {add:[...], remove:[...], target:applicant|applicantAction}}`."""
    body = {}
    if isinstance(v, dict):
        if v.get("add") is not None:
            body["tags"] = _list(v["add"])
        if v.get("remove") is not None:
            body["tagsToRemove"] = _list(v["remove"])
        if not body.get("tags") and not body.get("tagsToRemove"):
            raise ValueError("tag action needs 'add' and/or 'remove'")
        _set_target(body, v)
    else:
        body["tags"] = _list(v)
    return {"type": "tags", "tags": body}


def _build_notes_action(v) -> dict:
    """`{note: "text"}` or `{note: {text:"...", target:applicant|applicantAction}}`."""
    if isinstance(v, dict):
        text = v.get("text", v.get("note"))
        if not text:
            raise ValueError("note action needs 'text'")
        body = {"note": str(text)}
        _set_target(body, v)
    else:
        body = {"note": str(v)}
    return {"type": "notes", "notes": body}


def _set_target(body: dict, src: dict) -> None:
    tgt = src.get("target") or src.get("targetType")
    if tgt is None:
        return
    if tgt not in TARGET_TYPES:
        raise ValueError(f"targetType {tgt!r} not in {sorted(TARGET_TYPES)}")
    body["targetType"] = tgt


ACTION_ITEM_TYPES = {
    "tag":       _build_tags_action,
    "note":      _build_notes_action,
    "sourceKey": lambda v: {"type": "sourceKey", "sourceKey": {"sourceKey": str(v)}},
}


# ---------- condition validation ----------------------------------------------

# Maximum length of a single `lit` value in a condition argument. A literal longer
# than this almost always signals a mistake (an expression mistyped as a string, a
# pasted blob) rather than a real comparison value.
MAX_LIT_LENGTH = 1024


def _validate_condition_ops(cond) -> None:
    """Walk a hand-authored condition AST and:
      - reject any `op` not in the known operator set (catches typos and the reserved
        `call` op),
      - reject a top-level `Condition.negate` — it is not UI-supported; negate via
        the not* operators (notContains, notIn, notEmpty, ne, …) instead,
      - reject a `lit` value longer than MAX_LIT_LENGTH.
    `lit` values are passed through verbatim (the author supplies them already
    JSON-encoded, as the API stores them); this function does not transform them."""
    if not isinstance(cond, dict):
        return
    if cond.get("negate"):
        raise ValueError("top-level Condition.negate is not supported; use a not* operator instead")
    for branch in cond.get("or", []) or []:
        for crit in (branch.get("and", []) if isinstance(branch, dict) else []) or []:
            if not isinstance(crit, dict):
                continue
            op = crit.get("op")
            if op is not None:
                if op in RESERVED_OPERATORS:
                    raise ValueError(f"operator {op!r} is reserved and not exposed by this skill")
                if op not in OPERATORS:
                    raise ValueError(f"unknown operator {op!r}; allowed: {sorted(OPERATORS)}")
            for arg in crit.get("args", []) or []:
                if isinstance(arg, dict) and "lit" in arg and isinstance(arg["lit"], str) and len(arg["lit"]) > MAX_LIT_LENGTH:
                    raise ValueError(f"literal value exceeds the {MAX_LIT_LENGTH}-character limit ({len(arg['lit'])} chars)")


# ---------- node / edge / action builders -------------------------------------

def _build_action_item(item: dict) -> dict:
    """Convert a compact action item ({tag:...} / {note:...} / ...) to Sumsub shape."""
    if not isinstance(item, dict) or len(item) != 1:
        raise ValueError(f"action item must be a single-key dict; got {item!r}")
    key, val = next(iter(item.items()))
    if key not in ACTION_ITEM_TYPES:
        raise ValueError(
            f"unknown or unsupported action item kind {key!r}; allowed: {sorted(ACTION_ITEM_TYPES)}. "
            f"(kytCase is not author-supported yet; riskScore/recheck are not supported.)"
        )
    return ACTION_ITEM_TYPES[key](val)


def _build_node(spec: dict) -> dict:
    if "id" not in spec:
        raise ValueError(f"node missing 'id': {spec!r}")
    if "type" not in spec:
        raise ValueError(f"node {spec['id']!r} missing 'type'")
    node_type = spec["type"]
    if node_type not in KNOWN_NODE_TYPES:
        raise ValueError(f"node {spec['id']!r}: unknown type {node_type!r}; allowed: {sorted(KNOWN_NODE_TYPES)}")

    node = {"id": spec["id"], "type": node_type}
    if spec.get("name") is not None:
        node["name"] = spec["name"]
    if spec.get("description") is not None:
        node["description"] = str(spec["description"])

    if node_type in LEVEL_NODE_TYPES:
        level_name = spec.get("levelName") or (spec.get("applicantLevel") or {}).get("levelName")
        if not level_name:
            raise ValueError(f"node {spec['id']!r}: type {node_type} requires 'levelName'")
        node["applicantLevel"] = {"levelName": level_name}
        if spec.get("disableGoBack") is not None:
            node["disableGoBack"] = bool(spec["disableGoBack"])

    elif node_type in TRANSITION_NODE_TYPES:
        # actionApplicantTransition: hands the verification process back from an
        # action workflow to the default workflow, entering the named level.
        level_name = spec.get("levelName") or (spec.get("applicantLevel") or {}).get("levelName")
        if not level_name:
            raise ValueError(f"node {spec['id']!r}: type {node_type} requires 'levelName' (the default-workflow level to transition into)")
        node["applicantTransition"] = {"applicantLevel": {"levelName": level_name}}

    elif node_type in ACTIONS_NODE_TYPES:
        items_in = spec.get("actions") or []
        if not items_in:
            raise ValueError(f"node {spec['id']!r}: type {node_type} requires non-empty 'actions'")
        node["actions"] = {"items": [_build_action_item(it) for it in items_in]}

    elif node_type in REJECT_NODE_TYPES:
        labels = spec.get("labels")
        button_ids = spec.get("buttonIds")
        if not labels and not button_ids:
            raise ValueError(f"node {spec['id']!r}: type {node_type} requires 'labels' or 'buttonIds'")
        node["finalRejection"] = {}
        if labels:
            node["finalRejection"]["reviewRejectLabels"] = list(labels)
        if button_ids:
            node["finalRejection"]["reviewButtonIds"] = list(button_ids)

    elif node_type in CHOICE_NODE_TYPES or node_type in REVIEW_NODE_TYPES:
        pass  # only id / type / name / description

    # Pass-through unknown keys (escape hatch)
    handled = {"id", "type", "name", "description", "levelName", "applicantLevel",
               "actions", "labels", "buttonIds", "disableGoBack"}
    for k, v in spec.items():
        if k in handled or v is None:
            continue
        node[k] = v

    return node


def _build_edge(spec: dict, node_ids: set) -> dict:
    if "from" not in spec or "to" not in spec:
        raise ValueError(f"edge missing 'from'/'to': {spec!r}")
    if spec["from"] not in node_ids:
        raise ValueError(f"edge {spec!r}: 'from' id {spec['from']!r} not in nodes")
    if spec["to"] not in node_ids:
        raise ValueError(f"edge {spec!r}: 'to' id {spec['to']!r} not in nodes")

    edge = {"from": spec["from"], "to": spec["to"]}
    if spec.get("id"):
        edge["id"] = spec["id"]

    # reviewDecisions ('on:' is a shorthand for the real `reviewDecisions`)
    on = spec.get("on") or spec.get("reviewDecisions")
    if on is not None:
        on_list = _list(on)
        for v in on_list:
            if v not in REVIEW_DECISIONS:
                raise ValueError(f"edge {spec['from']}->{spec['to']}: reviewDecisions {v!r} not in {sorted(REVIEW_DECISIONS)}")
        edge["reviewDecisions"] = on_list

    # Guard the removed expression shortcuts so old specs fail loudly, not silently.
    for legacy in ("when", "whenRaw"):
        if legacy in spec:
            raise ValueError(
                f"edge {spec['from']}->{spec['to']}: '{legacy}:' is no longer supported. "
                f"Write the condition AST directly under 'condition:' "
                f"(e.g. {{op: eq, args: [{{exp: \"applicant.country\"}}, {{lit: \"\\\"USA\\\"\"}}]}}); see SKILL.md."
            )

    # condition: the real Sumsub AST, authored directly and passed through verbatim.
    if spec.get("condition") is not None:
        edge["condition"] = spec["condition"]
        try:
            _validate_condition_ops(edge["condition"])
        except ValueError as e:
            raise ValueError(f"edge {spec['from']}->{spec['to']}: {e}")

    return edge


# ---------- edge invariant: only choices branch ------------------------------

def _enforce_edge_invariant(nodes: list, edges: list) -> None:
    """Only `exclusiveChoice`/`actionExclusiveChoice` nodes may branch (>1 out-edge)
    or gate (`reviewDecisions`/`condition` on an out-edge). Every other node has at
    most one *unconditional* out-edge — a level/action transition is singular and
    plain.

    To branch a level's outcome, author an explicit choice and put the branches on
    *its* out-edges; the builder never synthesises a choice for you. `reviewDecisions`
    on a choice out-edge match the review decision of the upstream level.
    """
    type_of = {n["id"]: n["type"] for n in nodes}
    grouped = defaultdict(list)
    for e in edges:
        grouped[e["from"]].append(e)
    for nid, outs in grouped.items():
        if type_of.get(nid) in CHOICE_NODE_TYPES:
            continue
        if len(outs) > 1:
            raise ValueError(
                f"node {nid!r} has {len(outs)} out-edges — only an exclusiveChoice may "
                f"branch. Route its outcome through a choice: add an exclusiveChoice, point "
                f"{nid!r} at it with one plain edge, and put the branches on the choice's "
                f"out-edges."
            )
        gated = next(
            (e for e in outs if ("reviewDecisions" in e) or ("condition" in e)), None
        )
        if gated is not None:
            raise ValueError(
                f"edge {nid}->{gated['to']}: a {type_of.get(nid)!r} node's out-edge is "
                f"unconditional — it can't carry on:/condition. Branch the outcome at an "
                f"exclusiveChoice: {nid} -> <choice> (one plain edge), then put on:/condition "
                f"on the choice's out-edges."
            )


# ---------- top-level --------------------------------------------------------

# The API's `name` field is a fixed enum naming the *kind* of workflow. There is
# exactly one workflow of each kind; a save creates a new draft revision of it.
# Compact spec exposes this as `kind:`. (`title` exists in the schema but is unused
# by the engine, so the builder neither requires nor emits it.)
WORKFLOW_KINDS = ("default", "test", "actions")


def build_workflow(spec: dict) -> dict:
    kind = spec.get("kind", "default")
    if kind not in WORKFLOW_KINDS:
        raise ValueError(
            f"workflow 'kind' must be one of {WORKFLOW_KINDS}; got {kind!r}. "
            f"The API's `name` field is an enum (default/test/actions), not a slug."
        )

    nodes_in = spec.get("nodes") or []
    if not nodes_in:
        raise ValueError("workflow must have at least one node")

    nodes = [_build_node(n) for n in nodes_in]

    # Duplicate-id check
    dupes = [iid for iid, c in Counter(n["id"] for n in nodes).items() if c > 1]
    if dupes:
        raise ValueError(f"duplicate node ids: {dupes}")

    # kind/node-type coherence: action-* node types only in action workflows,
    # standard types only in verification workflows. Sumsub rejects mixes.
    if kind == "actions":
        non_action = [
            n["id"] for n in nodes if n["type"] not in ACTION_PREFIXED_NODE_TYPES
        ]
        if non_action:
            raise ValueError(
                f"kind='actions' workflow contains non-action node(s) {non_action}. "
                f"Inside an action workflow use the action-* node types "
                f"(actionApplicantLevel, actionExclusiveChoice, actionActions, "
                f"actionManualReview, actionFinalRejection, actionApplicantTransition)."
            )
    else:  # default / test — standard verification workflow
        action_only = [
            n["id"] for n in nodes if n["type"] in ACTION_PREFIXED_NODE_TYPES
        ]
        if action_only:
            raise ValueError(
                f"kind={kind!r} workflow contains action-* node(s) {action_only}. "
                f"Use standard node types (applicantLevel, exclusiveChoice, actions, "
                f"manualReview, finalRejection) for a verification workflow, or set "
                f"kind='actions' for a post-verification action workflow."
            )
        # `applicantAction` tag/note targeting is only available in action workflows,
        # because only there is the applicantAction in the evaluation context.
        bad_target = [
            n["id"] for n in nodes
            for it in (n.get("actions", {}).get("items", []) if n["type"] in ACTIONS_NODE_TYPES else [])
            for fam in ("tags", "notes")
            if it.get(fam, {}).get("targetType") == "applicantAction"
        ]
        if bad_target:
            raise ValueError(
                f"kind={kind!r} workflow uses targetType='applicantAction' on node(s) {bad_target}. "
                f"That target is only available inside an action workflow (kind='actions')."
            )

    node_ids = {n["id"] for n in nodes}
    edges_in = spec.get("edges") or []
    edges = [_build_edge(e, node_ids) for e in edges_in]

    # Only choice nodes may branch or gate; every other node has one plain out-edge.
    _enforce_edge_invariant(nodes, edges)

    # Every condition node should have ≥1 outgoing edge that actually branches —
    # a `condition` or a `reviewDecisions` ('on:') gate.
    for n in nodes:
        if n["type"] in CHOICE_NODE_TYPES:
            outs = [e for e in edges if e["from"] == n["id"]]
            if not outs:
                raise ValueError(f"condition node {n['id']!r} has no outgoing edges")
            if not any(("condition" in e) or ("reviewDecisions" in e) for e in outs):
                raise ValueError(
                    f"condition node {n['id']!r} must have at least one outgoing edge "
                    f"with a 'condition' clause or an 'on:' (reviewDecisions) gate"
                )

    revision_status = spec.get("revisionStatus", "draft")
    if revision_status != "draft":
        raise ValueError(
            f"revisionStatus must be 'draft' on create (got {revision_status!r}); "
            "the create/update POST only writes drafts — publishing is a separate, gated "
            "step via PUT /{id}/revisionStatus (see the skill's Danger section)"
        )

    payload = {
        "name": kind,
        "revisionStatus": revision_status,
        "nodes": nodes,
        "edges": edges,
    }
    # Preserve id for upsert (POST with existing id updates in place).
    if spec.get("id") is not None:
        payload["id"] = spec["id"]
    # UpsertApplicantWorkflowDto accepts only {name, nodes, edges, id, revision,
    # revisionStatus, title}. `notices` is response-only, `layout` is server
    # auto-arranged, and `desc` no longer exists in the schema — none are sent.
    return payload


def main():
    try:
        spec = json.load(sys.stdin)
    except ValueError as e:
        print(f"error: invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(2)
    try:
        payload = build_workflow(spec)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
