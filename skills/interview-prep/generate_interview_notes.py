#!/usr/bin/env python3
"""
Generate interview prep notes .docx from a structured content dict.

Usage:
    python3 skills/interview-prep/generate_interview_notes.py \
        --company "telus" \
        --role "data-strategist" \
        --content-file /tmp/interview_content.py \
        --output-dir job-outputs/interview-notes/

Content file format (/tmp/interview_content.py):
    content = {
        "company": "Telus",             # display name
        "role": "Data Strategist",      # display name
        "questions": [
            {
                "number": 1,
                "type": "Behavioural",
                "question": "Tell me about a time you led a complex data project.",
                "approach": "Use the Snowflake migration story. Lead with scope...",
                "story": {
                    "situation": "...",
                    "task": "...",
                    "action": "...",
                    "result": "...",
                    "reflection": "...",
                },
                "tip": "Keep the technical detail brief — they want leadership signals.",
            },
        ],
        "red_flag_questions": [
            {
                "question": "You've been independent for a few years — how do you work within a structure?",
                "why_asked": "Culture fit, coachability",
                "how_to_answer": "Reframe operator independence as a scaling asset...",
            },
        ],
        "company_research": [
            "Telus Health acquired LifeWorks in 2022 — now largest health benefits platform in Canada.",
            "Current focus: AI-driven health outcomes, reducing claims processing time.",
        ],
        "questions_to_ask": [
            "What does success look like for this role in the first 90 days?",
            "How does the data team interface with product and engineering?",
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
    lib_path = os.path.normpath(os.path.join(SCRIPT_DIR, '../../.claude/lib'))
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)


_setup_lib_path()

from project_paths import get_project_root   # noqa: E402
from docx_helpers import set_metadata        # noqa: E402
from docx import Document                    # noqa: E402
from docx.shared import Inches, Pt, RGBColor # noqa: E402
from docx.oxml.ns import qn                  # noqa: E402
from docx.oxml import OxmlElement            # noqa: E402

FONT = "Arial"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_content(content_file):
    spec   = importlib.util.spec_from_file_location("interview_content", content_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'content'):
        raise ValueError(f"content_file must define a variable named 'content': {content_file}")
    return module.content


def add_divider(doc, color="CCCCCC", size=6):
    """Add a light horizontal rule between sections."""
    p   = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr   = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'),   'single')
    bottom.set(qn('w:sz'),    str(size))
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), color)
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def fix_heading_font(heading):
    """Override Word's heading theme font to Arial."""
    for run in heading.runs:
        run.font.name = FONT


def add_body_para(doc, text, bold_prefix=None, italic=False):
    """
    Add a plain body paragraph. Optionally bold a prefix label.
    E.g. add_body_para(doc, "Led migration...", bold_prefix="Situation: ")
    """
    p = doc.add_paragraph()
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        r.font.name = FONT
        r.font.size = Pt(11)
    r2 = p.add_run(text)
    r2.italic = italic
    r2.font.name = FONT
    r2.font.size = Pt(11)
    return p


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------

def build_interview_notes(doc, content, project_root):
    """Populate doc with interview prep content."""
    set_metadata(doc, project_root)

    company = content.get("company", "")
    role    = content.get("role", "")
    today   = date.today().strftime("%B %-d, %Y")

    # Set margins
    for section in doc.sections:
        section.top_margin    = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin   = Inches(1)
        section.right_margin  = Inches(1)

    # Document title
    title = doc.add_heading(f"Interview Prep — {role} at {company}", level=1)
    fix_heading_font(title)
    doc.add_paragraph(today).runs[0].font.name = FONT

    # ---- Part 1: Question list table ----
    questions = content.get("questions", [])
    if questions:
        add_divider(doc)
        h = doc.add_heading("Part 1 — Top Interview Questions", level=2)
        fix_heading_font(h)

        table = doc.add_table(rows=1, cols=3)
        table.style = "Table Grid"
        hdr = table.rows[0].cells
        hdr[0].text = "#"
        hdr[1].text = "Type"
        hdr[2].text = "Question"
        for cell in hdr:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.bold = True
                    run.font.name = FONT
        # Col widths: 0.4 | 1.1 | 5.0
        for row_data in questions:
            row = table.add_row().cells
            row[0].width = Inches(0.4)
            row[1].width = Inches(1.1)
            row[2].width = Inches(5.0)
            row[0].text = str(row_data.get("number", ""))
            row[1].text = row_data.get("type", "")
            row[2].text = row_data.get("question", "")
            for cell in row:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.name = FONT

    # ---- Part 2: STAR stories ----
    if questions:
        add_divider(doc)
        h = doc.add_heading("Part 2 — STAR Story Bank", level=2)
        fix_heading_font(h)

        for q in questions:
            story = q.get("story")
            if not story:
                continue
            qh = doc.add_heading(f"Q{q.get('number', '')} — {q.get('question', '')}", level=3)
            fix_heading_font(qh)

            approach = q.get("approach", "")
            if approach:
                add_body_para(doc, approach, bold_prefix="Approach: ")

            for label in ("situation", "task", "action", "result", "reflection"):
                text = story.get(label, "")
                if text:
                    prefix = "★ Reflection: " if label == "reflection" else f"{label.capitalize()}: "
                    add_body_para(doc, text, bold_prefix=prefix)

            tip = q.get("tip", "")
            if tip:
                add_body_para(doc, f"💡 Tip: {tip}", italic=True)

    # ---- Part 3: Company research ----
    research = content.get("company_research", [])
    if research:
        add_divider(doc)
        h = doc.add_heading("Part 3 — Company Research", level=2)
        fix_heading_font(h)
        for item in research:
            doc.add_paragraph(item, style="List Bullet").runs[0].font.name = FONT if doc.paragraphs[-1].runs else None

    # ---- Part 4: Red-flag questions ----
    red_flags = content.get("red_flag_questions", [])
    if red_flags:
        add_divider(doc)
        h = doc.add_heading("Part 4 — Red-Flag Questions", level=2)
        fix_heading_font(h)

        table = doc.add_table(rows=1, cols=3)
        table.style = "Table Grid"
        hdr = table.rows[0].cells
        hdr[0].text = "Question"
        hdr[1].text = "Why It's Asked"
        hdr[2].text = "How to Answer It"
        for cell in hdr:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.bold = True
                    run.font.name = FONT

        for rf in red_flags:
            row = table.add_row().cells
            row[0].text = rf.get("question", "")
            row[1].text = rf.get("why_asked", "")
            row[2].text = rf.get("how_to_answer", "")
            for cell in row:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.name = FONT

    # ---- Part 5: Questions to ask ----
    questions_to_ask = content.get("questions_to_ask", [])
    if questions_to_ask:
        add_divider(doc)
        h = doc.add_heading("Part 5 — Questions to Ask", level=2)
        fix_heading_font(h)
        for item in questions_to_ask:
            p = doc.add_paragraph(item, style="List Bullet")
            if p.runs:
                p.runs[0].font.name = FONT

    # Footer prompt
    add_divider(doc)
    p = doc.add_paragraph()
    r = p.add_run(f"Ready to practise live? Run /mock-interview for {role} at {company}.")
    r.italic = True
    r.font.name = FONT
    r.font.size = Pt(10)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate interview prep notes docx")
    parser.add_argument("--company",      required=True)
    parser.add_argument("--role",         required=True)
    parser.add_argument("--content-file", required=True)
    parser.add_argument("--output-dir",   required=False)
    args = parser.parse_args()

    try:
        project_root = get_project_root()
    except RuntimeError as e:
        print(f"ERROR:{e}", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(project_root, "job-outputs", "interview-notes")
    os.makedirs(output_dir, exist_ok=True)

    today     = date.today().strftime("%Y-%m-%d")
    filename  = f"interview_{args.company}_{args.role}_{today}"
    docx_path = os.path.join(output_dir, filename + ".docx")

    try:
        content = load_content(args.content_file)
    except Exception as e:
        print(f"ERROR:Failed to load content file: {e}", file=sys.stderr)
        sys.exit(1)

    doc = Document()

    try:
        build_interview_notes(doc, content, project_root)
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
