#!/usr/bin/env python3
"""OPTIONAL fallback — render a regulation PDF to per-page PNGs for visual reading.

You usually DON'T need this: the Claude Code Read tool reads PDFs natively (it renders
pages and extracts text, no library required) — just Read the PDF directly, in page
ranges for long docs. Reach for this script only when you want explicit DPI control on
a scanned / image-only PDF, or native PDF reading struggles on a specific file. Some
docx->pdf exports have outlined/imaged text that flat text extractors miss (pypdf got
483 chars from a real 27-page questionnaire) — but the Read tool renders those fine too.

    python3 render_regulation.py <regulation.pdf> [out_dir] [--dpi N]

Prints, one per line, the PNG paths to read (in order). The agent then Reads each
page image and extracts requirements into requirements.json (see SKILL.md).

Requires PyMuPDF (`pip install pymupdf`). If it's not installed, do NOT block on
installing it — just Read the PDF directly with the Read tool.
"""
import os
import sys


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.stderr.write("usage: render_regulation.py <regulation.pdf> [out_dir] [--dpi N]\n")
        return 2
    pdf = args[0]
    out_dir = args[1] if len(args) > 1 else "/tmp/regpages"
    dpi = 110
    for a in sys.argv[1:]:
        if a.startswith("--dpi"):
            dpi = int(a.split("=", 1)[1]) if "=" in a else 110

    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.stderr.write("PyMuPDF not installed. Run: python3 -m pip install pymupdf\n")
        return 3

    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf)
    paths = []
    for i in range(doc.page_count):
        p = os.path.join(out_dir, f"p{i:02d}.png")
        doc[i].get_pixmap(dpi=dpi).save(p)
        paths.append(p)
    sys.stderr.write(f"rendered {len(paths)} page(s) at {dpi} dpi -> {out_dir}\n")
    print("\n".join(paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
