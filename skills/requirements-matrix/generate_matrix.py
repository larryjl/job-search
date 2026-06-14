#!/usr/bin/env python3
"""
Generate a requirements response matrix .docx from a structured content dict.

Usage:
    python3 skills/requirements-matrix/generate_matrix.py \
        --organisation "government-of-alberta" \
        --role "senior-data-architect" \
        --content-file /tmp/matrix_content.py \
        --output-dir job-outputs/matrices/

Content file format (/tmp/matrix_content.py):
    content = {
        "organisation": "Government of Alberta",   # display name (title case)
        "role": "Senior Data Architect",            # display name
        "mandatory": [
            {
                "label": "M1",
                "wording": "Minimum 7 years experience with enterprise data platforms...",
                "verdict": "Met.",
                "summary": "7+ years across three roles.",   # one-sentence summary after verdict
                "bullets": [
                    "ACME Corp, Senior Analyst (2019–2025): Led design of Snowflake data warehouse...",
                    "Previous Co, Data Analyst (2016–2019): Built ETL pipelines supporting...",
                ],
            },
        ],
        "scored": [
            {
                "label": "S1",
                "wording": "Experience with cloud-native data platforms (AWS, Azure, GCP)...",
                "verdict": "Met.",
                "summary": "AWS and Azure experience across multiple production deployments.",
                "bullets": [...],
            },
        ],
    }

Output:
    Prints SAVED:/path/to/file.docx on success.
    Prints ERROR:... and exits with code 1 on failure.
"""

import argparse
import importlib.util
import os
import sys
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _setup_lib_path():
    lib_path = os.path.normpath(os.path.join(SCRIPT_DIR, '../lib'))
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)


_setup_lib_path()

from project_paths import get_project_root   # noqa: E402
from docx_helpers import (                   # noqa: E402
    NAVY, BLACK,
    set_spacing, add_run, set_margins, keep_with_next,
    add_rule, add_bullet, set_metadata,
)
from docx import Document                    # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_content(content_file):
    spec   = importlib.util.spec_from_file_location("matrix_content", content_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'content'):
        raise ValueError(f"content_file must define a variable named 'content': {content_file}")
    return module.content


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------

def add_section_heading(doc, text):
    """ALL-CAPS section heading: 12pt bold NAVY."""
    p = doc.add_paragraph()
    set_spacing(p, before=8, after=4)
    keep_with_next(p)
    add_run(p, text.upper(), bold=True, size=12, color=NAVY)
    return p


def add_requirement(doc, req):
    """Render one requirement block: label, verdict line, bullets."""
    # Requirement label + wording (bold, 11pt BLACK)
    p = doc.add_paragraph()
    set_spacing(p, before=8, after=2)
    keep_with_next(p)
    label_text = f"{req['label']} — {req['wording']}"
    add_run(p, label_text, bold=True, size=11)

    # Verdict line + summary (bold, 11pt BLACK)
    verdict_text = req.get("verdict", "")
    summary_text = req.get("summary", "")
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=2)
    keep_with_next(p)
    full_verdict = verdict_text
    if summary_text:
        full_verdict += f" {summary_text}"
    add_run(p, full_verdict, bold=True, size=11)

    # Bullet points
    for bullet_text in req.get("bullets", []):
        add_bullet(doc, bullet_text)

    # Spacer
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=6)


def build_matrix(doc, content, project_root):
    """Populate doc with requirements matrix content."""
    candidate_name = set_metadata(doc, project_root)

    organisation = content.get("organisation", "")
    role         = content.get("role", "")
    today_str    = date.today().strftime("%B %-d, %Y")

    # --- Title block ---
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=2)
    add_run(p, candidate_name, bold=True, size=16, color=NAVY)

    if organisation and role:
        p = doc.add_paragraph()
        set_spacing(p, before=0, after=8)
        add_run(p, f"{organisation} — {role}", size=12)

    p = doc.add_paragraph()
    set_spacing(p, before=0, after=2)
    add_run(p, "Requirement Response Matrix", size=12)

    p = doc.add_paragraph()
    set_spacing(p, before=0, after=8)
    add_run(p, today_str, size=12)

    add_rule(doc)

    # --- Mandatory requirements ---
    mandatory = content.get("mandatory", [])
    if mandatory:
        add_section_heading(doc, "Mandatory Requirements")
        for req in mandatory:
            add_requirement(doc, req)

        add_rule(doc)

    # --- Scored requirements ---
    scored = content.get("scored", [])
    if scored:
        add_section_heading(doc, "Scored Requirements")
        for req in scored:
            add_requirement(doc, req)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate requirements matrix docx")
    parser.add_argument("--organisation", required=True, help="Normalised org slug (e.g. 'government-of-alberta')")
    parser.add_argument("--role",         required=True, help="Normalised role slug (e.g. 'senior-data-architect')")
    parser.add_argument("--content-file", required=True)
    parser.add_argument("--output-dir",   required=False)
    args = parser.parse_args()

    try:
        project_root = get_project_root()
    except RuntimeError as e:
        print(f"ERROR:{e}", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(project_root, "job-outputs", "matrices")
    os.makedirs(output_dir, exist_ok=True)

    today     = date.today().strftime("%Y-%m-%d")
    filename  = f"matrix_{args.organisation}_{args.role}_{today}"
    docx_path = os.path.join(output_dir, filename + ".docx")

    try:
        content = load_content(args.content_file)
    except Exception as e:
        print(f"ERROR:Failed to load content file: {e}", file=sys.stderr)
        sys.exit(1)

    doc = Document()
    set_margins(doc)

    try:
        build_matrix(doc, content, project_root)
    except Exception as e:
        print(f"ERROR:Document build failed: {e}", file=sys.stderr)
        sys.exit(1)

    doc.save(docx_path)

    try:
        Document(docx_path)
    except Exception as e:
        print(f"ERROR:Generated docx failed validation: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"SAVED:{docx_path}")


if __name__ == "__main__":
    main()
