"""Text extraction utilities for job postings."""

import subprocess
import os
import re


def extract_job_details_from_pdf(pdf_path):
    """
    Extract company name and job title from a PDF file.

    Uses pdftotext to extract text from the first ~500 characters.
    Attempts to identify the job title and company name from common patterns.

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        tuple: (company_name, job_title) or (None, None) if extraction fails
    """
    try:
        result = subprocess.run(
            ["pdftotext", pdf_path, "-"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None, None

        text = result.stdout[:1000]  # First ~1000 chars

        # Try to find patterns like "Senior Software Engineer at Acme Corp"
        # or "Senior Software Engineer — Acme Corp"
        match = re.search(
            r'([^—\n]+?)\s+(?:at|—)\s+([^—\n]+?)(?:\n|$)',
            text,
            re.IGNORECASE
        )
        if match:
            job_title = match.group(1).strip()
            company = match.group(2).strip()
            return company, job_title

        # Fallback: first line might be title, second might be company
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if len(lines) >= 2:
            return lines[1], lines[0]

        return None, None

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None, None


def extract_candidate_name():
    """
    Extract candidate name from profile/master-resume.md.

    The first line should be "# [Candidate Name]".

    Returns:
        str: Candidate name or "Unknown" if not found

    Raises:
        FileNotFoundError: If profile/master-resume.md doesn't exist
    """
    try:
        from .project_paths import get_profile_resume
    except ImportError:
        from project_paths import get_profile_resume

    try:
        with open(get_profile_resume()) as f:
            first_line = f.readline()
            # Strip "# " prefix and whitespace
            name = first_line.lstrip("# ").strip()
            return name if name else "Unknown"
    except FileNotFoundError:
        raise FileNotFoundError(
            "profile/master-resume.md not found. "
            "Please add your resume to profile/master-resume.md before running skills."
        )


def strip_html(html: str) -> str:
    """
    Strip HTML tags and entities from a string, collapsing whitespace.

    Used to convert raw ATS job description HTML to plain text for scoring
    and display. Handles tags, numeric/named HTML entities, and excess whitespace.

    Args:
        html (str): Raw HTML string

    Returns:
        str: Plain text with tags and entities removed
    """
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&[a-z#0-9]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_job_details_from_html(html_text):
    """
    Extract company name and job title from raw HTML text.

    Looks for <title>, <h1>, or structured data patterns.

    Args:
        html_text (str): Raw HTML content

    Returns:
        tuple: (company_name, job_title) or (None, None)
    """
    # Try <title> tag
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_text)
    if title_match:
        title_text = title_match.group(1).strip()
        # Often formatted as "Job Title - Company Name"
        if " - " in title_text:
            parts = title_text.split(" - ", 1)
            return parts[1].strip(), parts[0].strip()

    # Try <h1> tag
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_text)
    if h1_match:
        return None, h1_match.group(1).strip()

    return None, None
