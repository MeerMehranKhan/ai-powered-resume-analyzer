"""Helpers for loading bundled demo content."""

from __future__ import annotations

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def load_demo_resume_text() -> str:
    """Load the bundled sample resume text."""

    return (ASSETS_DIR / "sample_resume.txt").read_text(encoding="utf-8")


def load_demo_job_description() -> str:
    """Load the bundled sample job description."""

    return (ASSETS_DIR / "sample_job_description.txt").read_text(encoding="utf-8")
