# Device Intelligence — signals, risk labels, and where they surface

Device Intelligence (the Fisherman module) is powered by Fingerprint device-ID
technology. It produces a **stable device identifier** plus a set of **device
risk labels** that feed Applicant Risk Scoring.

## Signal categories captured

| Category | Examples |
|---|---|
| Identity | stable `visitorId` device fingerprint (lets you recognise returning devices) |
| Tampering | device emulation, virtual machine, rooted / jailbroken device, dev-tools open |
| Network | VPN / proxy usage, location / timezone spoofing, IP mismatch |
| Automation | bot activity, browser automation, headless browser |
| Privacy | incognito / private browsing, signal-blocking extensions |
| Correlation | reused device across applicants (`manyApplicantsSameDevice`), multiple devices used (`multipleDevices`), multi-accounting |

## Risk labels

Device risk labels are a subset of Sumsub **applicant risk labels**. The
canonical, versioned list lives in the docs — do not hardcode a copy that will
drift:

- Device risk labels: <https://docs.sumsub.com/docs/applicant-risk-labels#device-risk-labels>

Typical device labels you will see (exact Sumsub label keys in parentheses):
device reused across applicants (`manyApplicantsSameDevice`), multiple devices
used (`multipleDevices`), VPN (`vpnUsage`) or TOR (`torUsage`), emulator
(`emulator`) or virtual machine (`virtualMachine`), rooted (`rooted`) / jailbroken
(`jailbroken`), bot / automation (`badBot`), tampering (`tampering`), incognito
(`incognito`). Each label is
either **blocking** (you refuse / step-up the user) or **informational** (you log
it) — that policy is yours to set; Sumsub only reports the labels.

## Where each result surfaces

| Surface | What you see | Use |
|---|---|---|
| Dashboard → applicant **Devices** tab | every device + its risk labels | manual review |
| Dashboard → verification result **Device Check** block | device summary for that check | manual review |
| Dashboard → **Transactions** → row → **View device details** | full per-event device detail | ongoing-monitoring review |
| `applicantReviewed` webhook | verdict only (`reviewResult`) — labels live on the applicant, not the payload | trigger to fetch the applicant (row below) |
| `GET /resources/applicants/{applicantId}/one` | applicant incl. device risk labels (`riskLabels.device`) | on-demand server check |

## How signals feed scoring

Device signals are combined with other factors (documents, AML, behaviour) into
the **Applicant Risk Score**. You can also write **fraud / risk rules** that fire
on specific device labels (e.g. "reused device across N applicants" → manual
review). Rule authoring is a dashboard task, not part of this skill.

## Reading vs trusting

As with all WebSDK signals: the browser-side capture is input, not verdict.
Trust the **server-side** read — the webhook delivery or the authenticated
applicant GET — for any access decision. The device labels you act on must come
from there, never from a value the browser reports back to you.
