"""Shared utilities for job-search skills."""

from .project_paths import get_project_root, get_postings_dir, get_profile_resume, get_jobs_csv
from .filename_builder import make_filename
from .extractors import extract_job_details_from_pdf, extract_candidate_name, extract_job_details_from_html
from .pdf_converter import url_to_pdf
from .http_client import fetch_json_curl, fetch_url_urllib
from .extractors import strip_html

__all__ = [
    "get_project_root",
    "get_postings_dir",
    "get_profile_resume",
    "get_jobs_csv",
    "make_filename",
    "extract_job_details_from_pdf",
    "extract_candidate_name",
    "extract_job_details_from_html",
    "url_to_pdf",
    "fetch_json_curl",
    "fetch_url_urllib",
    "strip_html",
]
