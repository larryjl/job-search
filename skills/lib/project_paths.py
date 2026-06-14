"""Project path resolution utilities."""

import subprocess
import os


def get_project_root():
    """
    Find the job-search project root by scanning mounts for CLAUDE.md + skills/.

    Returns:
        str: Path to the project root

    Raises:
        RuntimeError: If project root cannot be found
    """
    result = subprocess.run(
        ["bash", "-c", "mount | awk '{print $3}'"],
        capture_output=True,
        text=True,
    )
    for mount in result.stdout.splitlines():
        if (os.path.exists(os.path.join(mount, "CLAUDE.md"))
                and os.path.isdir(os.path.join(mount, "skills"))):
            return mount
    raise RuntimeError(
        "job-search project root not found. Connect the project folder "
        "(containing CLAUDE.md and skills/) to this session."
    )


def get_postings_dir():
    """
    Get the postings directory path.

    Returns:
        str: Path to job-outputs/postings/
    """
    project_root = get_project_root()
    postings_dir = os.path.join(project_root, "job-outputs", "postings")
    os.makedirs(postings_dir, exist_ok=True)
    return postings_dir


def get_profile_resume():
    """
    Get the path to the master resume file.

    Returns:
        str: Path to profile/master-resume.md
    """
    project_root = get_project_root()
    return os.path.join(project_root, "profile", "master-resume.md")


def get_jobs_csv():
    """
    Get the path to jobs.csv.

    Returns:
        str: Path to job-outputs/jobs.csv
    """
    project_root = get_project_root()
    return os.path.join(project_root, "job-outputs", "jobs.csv")
