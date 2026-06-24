"""
Project path resolution for job-search skills.

Skills run inside a Claude Code sandbox whose working directory is an ephemeral
output folder, NOT the job-search project directory the user has mounted.  This
module locates the real project root by scanning mounted filesystems for the
two markers that uniquely identify it: a CLAUDE.md file and a skills/ directory.

All other path helpers in this module call get_project_root() and build paths
relative to it, so skills never hard-code absolute paths.

Note: all functions in this module return plain str paths rather than
pathlib.Path objects. This keeps them compatible with existing callers that
pass paths directly to os.path functions, subprocess, open(), and similar
APIs — all of which accept str without any conversion.
"""

import subprocess
import os


def get_project_root() -> str:
    """
    Find the job-search project root by scanning active filesystem mounts.

    The Claude sandbox mounts the user's connected folder somewhere under a
    session-specific path.  Rather than guessing that path, we ask the OS for
    every currently mounted filesystem and test each one for the two markers
    that identify the job-search project: CLAUDE.md and a skills/ directory.

    Returns:
        str: Absolute path to the project root directory.

    Raises:
        RuntimeError: If no mount point contains both CLAUDE.md and skills/.
    """
    # Ask the OS for all active mount points; awk extracts the 3rd field
    # (the mount-point path) from each line of `mount` output.
    # Example mount line: "/dev/sda1 on /mnt/data type ext4 (rw,relatime)"
    #   → $1="/dev/sda1"  $2="on"  $3="/mnt/data"  (field 3 is the mount point)
    result = subprocess.run(
        ["bash", "-c", "mount | awk '{print $3}'"],
        # capture_output=True: redirect stdout and stderr to result.stdout /
        # result.stderr instead of printing them to the terminal.
        # text=True: decode the output bytes to a Python str automatically;
        # without this you'd get b"..." bytes objects instead of strings.
        capture_output=True,
        text=True,
    )

    for mount in result.stdout.splitlines():
        # A valid project root must have BOTH markers present.
        has_claude_md = os.path.exists(os.path.join(mount, "CLAUDE.md"))
        has_skills_dir = os.path.isdir(os.path.join(mount, "skills"))

        if has_claude_md and has_skills_dir:
            return mount  # Found it — return immediately.

    raise RuntimeError(
        "job-search project root not found. Connect the project folder "
        "(containing CLAUDE.md and skills/) to this session."
    )


def get_postings_dir() -> str:
    """
    Return the path to the job postings output directory, creating it if needed.

    Postings are PDFs saved by job-scout and save-job-posting.  The directory
    is created on first access so skills don't have to check themselves.

    Returns:
        str: Absolute path to job-outputs/postings/.
    """
    project_root = get_project_root()
    postings_dir = os.path.join(project_root, "job-outputs", "postings")

    # exist_ok=True means this is a no-op if the directory already exists.
    os.makedirs(postings_dir, exist_ok=True)

    return postings_dir


def get_profile_resume() -> str:
    """
    Return the path to the candidate's master resume Markdown file.

    Skills read this file to extract the candidate name and resume content.
    The file is expected at profile/master-resume.md relative to the project
    root; this function does NOT check whether the file exists — callers that
    need it to exist should handle FileNotFoundError themselves.

    Returns:
        str: Absolute path to profile/master-resume.md.
    """
    project_root = get_project_root()
    return os.path.join(project_root, "profile", "master-resume.md")


def get_jobs_csv() -> str:
    """
    Return the path to the application tracking spreadsheet (jobs.csv).

    All skills that log or read application status use this path.  The file
    is not created here — skills are responsible for initialising it if absent.

    Returns:
        str: Absolute path to job-outputs/jobs.csv.
    """
    project_root = get_project_root()
    return os.path.join(project_root, "job-outputs", "jobs.csv")
