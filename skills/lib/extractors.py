"""
Text extraction utilities for job-search skills.

This module provides four functions for pulling structured information out of
job posting files and the candidate's master resume:

    extract_job_details_from_pdf(pdf_path)
        → (company, title) from a saved PDF posting.

    extract_candidate_name()
        → candidate's name from profile/master-resume.md.

    strip_html(html)
        → plain text from raw HTML (removes tags and entities).

    extract_job_details_from_html(html_text)
        → (company, title) from a raw HTML page string.

All functions return graceful fallbacks (None, "Unknown", empty string) rather
than raising on malformed input, so skills can degrade cleanly when extraction
is uncertain.
"""

import subprocess
import os
import re


def extract_job_details_from_pdf(pdf_path: str):
    """
    Extract company name and job title from the first page of a PDF posting.

    Uses the system `pdftotext` utility (poppler-utils) to convert the PDF to
    plain text, then applies regex and heuristic line-parsing to identify the
    job title and company.

    Args:
        pdf_path (str): Absolute path to the PDF file to parse.

    Returns:
        tuple[str | None, str | None]: (company_name, job_title).
            Returns (None, None) if pdftotext fails, the file is not found,
            or no recognisable pattern is detected.
    """
    try:
        # Run pdftotext with "-" as the output path to stream text to stdout.
        result = subprocess.run(
            ["pdftotext", pdf_path, "-"],
            capture_output=True,
            text=True,
            timeout=10,   # Avoid hanging on large/corrupt PDFs.
        )

        # A non-zero return code means pdftotext couldn't read the file.
        if result.returncode != 0:
            return None, None

        # Limit to the first 1000 characters — the header area usually contains
        # the title and company; reading more adds noise without value.
        text = result.stdout[:1000]

        # Pattern 1: "Job Title at Company Name" or "Job Title — Company Name"
        #
        # Breakdown:
        #   ([^—\n]+?)   — capture group 1: one or more characters that are NOT
        #                  an em-dash (—) or newline; the `?` makes it non-greedy
        #                  so it stops at the first separator rather than the last.
        #                  [^...] is a negated character class — it matches any
        #                  character EXCEPT the ones listed.
        #   \s+          — one or more whitespace chars around the separator
        #   (?:at|—)     — non-capturing group ((?:...)) matching the literal word
        #                  "at" or an em-dash; non-capturing means this group is
        #                  not included in match.group() numbering.
        #   \s+          — whitespace after the separator
        #   ([^—\n]+?)   — capture group 2: the company name (same rules as group 1)
        #   (?:\n|$)     — non-capturing group: match ends at a newline or end-of-string
        #
        # Plain English: match "anything [not em-dash/newline] THEN 'at' or '—'
        # THEN anything [not em-dash/newline] up to end-of-line."
        match = re.search(
            r"([^—\n]+?)\s+(?:at|—)\s+([^—\n]+?)(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if match:
            # Group 1 is the job title; group 2 is the company.
            job_title = match.group(1).strip()
            company = match.group(2).strip()
            return company, job_title

        # Fallback: if no separator pattern matched, assume the first
        # non-empty line is the job title and the second is the company.
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if len(lines) >= 2:
            # Return order is (company, title): lines[0] is the title (first line
            # of the JD header) but callers expect (company, title), so it goes second.
            return lines[1], lines[0]

        # Not enough content to make a guess.
        return None, None

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # TimeoutExpired: pdftotext took too long (corrupt or huge PDF).
        # FileNotFoundError: pdftotext binary is not installed.
        return None, None


def extract_candidate_name() -> str:
    """
    Read the candidate's name from the first line of profile/master-resume.md.

    The master resume is expected to start with a Markdown H1 heading:
        # Lawrence Lee

    The "# " prefix is stripped to return just the name.

    Returns:
        str: Candidate name, or "Unknown" if the first line is empty.

    Raises:
        FileNotFoundError: If profile/master-resume.md does not exist.
    """
    # Dual-mode import: when this module is loaded as part of the `lib`
    # package (e.g. `from lib import extract_candidate_name`), the relative
    # import works.  When a skill adds skills/lib to sys.path and imports
    # the module directly (e.g. `import extractors`), the relative import
    # fails with ImportError, so we fall back to a plain absolute import.
    # Note: this isn't handling a missing module — both paths point to the
    # same file (project_paths.py); which one succeeds depends on how Python
    # resolved this file's location (as a package import vs. a direct script).
    try:
        from .project_paths import get_profile_resume
    except ImportError:
        from project_paths import get_profile_resume  # sys.path fallback

    try:
        with open(get_profile_resume()) as f:
            first_line = f.readline()
            # lstrip("# ") strips any combination of '#' and space characters
            # from the left side of the string (not the literal two-character
            # sequence "# "). So "## Name" becomes "Name", and "# Name" also
            # becomes "Name" — both heading levels are handled correctly.
            name = first_line.lstrip("# ").strip()
            return name if name else "Unknown"
    except FileNotFoundError:
        raise FileNotFoundError(
            "profile/master-resume.md not found. "
            "Please add your resume to profile/master-resume.md before running skills."
        )


def strip_html(html: str) -> str:
    """
    Convert raw HTML to plain text by removing tags and decoding entities.

    Used by ATS-scraping skills (scout-adzuna, scout-link, etc.) to turn raw
    job description HTML into clean text that can be scored by the filter or
    displayed to the user.

    Processing steps (in order):
      1. Replace every HTML tag with a space so adjacent words don't merge.
      2. Replace HTML entities (e.g. &amp;, &#39;, &nbsp;) with a space.
      3. Collapse all runs of whitespace into a single space and trim ends.

    Args:
        html (str): Raw HTML string, possibly containing tags and entities.

    Returns:
        str: Plain text with all markup removed and whitespace normalised.
    """
    # Step 1: remove tags — <[^>]+> matches any tag, including attributes.
    text = re.sub(r"<[^>]+>", " ", html)

    # Step 2: remove entities — covers named (&amp;), decimal (&#39;),
    # and hex (&#x2019;) forms via the broad [a-z#0-9]+ character class.
    text = re.sub(r"&[a-z#0-9]+;", " ", text)

    # Step 3: collapse newlines, tabs, and multiple spaces into one space.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_job_details_from_html(html_text: str):
    """
    Extract company name and job title from a raw HTML page string.

    Tries two strategies in order:
      1. Parse the <title> element, which many ATS pages format as
         "Job Title - Company Name".
      2. Fall back to the first <h1> element for the job title (company unknown).

    Args:
        html_text (str): Full HTML source of the job posting page.

    Returns:
        tuple[str | None, str | None]: (company_name, job_title).
            company_name is None if it could not be determined.
            Both are None if no recognisable pattern was found.
    """
    # Strategy 1: <title> tag — often the most reliable structured source.
    title_match = re.search(r"<title[^>]*>([^<]+)</title>", html_text)
    if title_match:
        title_text = title_match.group(1).strip()

        # Many ATS pages use the format "Job Title - Company Name".
        # Split on the first " - " only (maxsplit=1) to avoid splitting
        # hyphenated company names like "Coca-Cola - Senior Analyst".
        if " - " in title_text:
            parts = title_text.split(" - ", 1)
            return parts[1].strip(), parts[0].strip()  # (company, title)

    # Strategy 2: first <h1> tag — usually the job title on a posting page.
    # Company cannot be reliably inferred from the heading alone.
    h1_match = re.search(r"<h1[^>]*>([^<]+)</h1>", html_text)
    if h1_match:
        return None, h1_match.group(1).strip()  # company unknown

    # Neither strategy produced a result.
    return None, None
