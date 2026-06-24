"""
skills/lib — Shared utility package for all job-search skills.

This package centralises the helpers that every skill needs so logic is never
duplicated across skill scripts.  Import from here rather than from individual
modules:

    from lib import make_filename, get_project_root, url_to_pdf

Modules in this package
-----------------------
project_paths   — Locate the job-search project root and canonical file paths
                  (postings dir, master resume, jobs.csv).
filename_builder— Build normalised output filenames (company + role + date).
extractors      — Extract text from PDFs, HTML, and the master resume.
pdf_converter   — Convert a fetched web page (HTML) to a saved PDF file.
http_client     — Thin wrappers around curl and urllib for HTTP GET requests.
"""

# ── project_paths: root discovery + canonical path helpers ───────────────────
from .project_paths import get_project_root, get_postings_dir, get_profile_resume, get_jobs_csv

# ── filename_builder: single source of truth for output filenames ─────────────
from .filename_builder import make_filename

# ── extractors: text extraction from PDFs, HTML, and the master resume ───────
from .extractors import (
    extract_job_details_from_pdf,
    extract_candidate_name,
    extract_job_details_from_html,
    strip_html,
)

# ── pdf_converter: save a live web page as a PDF posting file ────────────────
from .pdf_converter import url_to_pdf

# ── http_client: low-level HTTP helpers (curl + urllib fallback) ──────────────
from .http_client import fetch_json_curl, fetch_url_urllib

__all__ = [
    # path helpers
    "get_project_root",
    "get_postings_dir",
    "get_profile_resume",
    "get_jobs_csv",
    # filename normalisation
    "make_filename",
    # text extraction
    "extract_job_details_from_pdf",
    "extract_candidate_name",
    "extract_job_details_from_html",
    "strip_html",
    # PDF generation
    "url_to_pdf",
    # HTTP helpers
    "fetch_json_curl",
    "fetch_url_urllib",
]
