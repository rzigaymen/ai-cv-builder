"""Create or inspect a deterministic job-application output folder."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def filesystem_safe(value: str, *, fallback: str) -> str:
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s-]+", "_", value.strip())
    return value.strip("_") or fallback


def job_folder_name(company: str, title: str) -> str:
    return "{}_{}".format(
        filesystem_safe(company, fallback="Company"),
        filesystem_safe(title, fallback="Job"),
    )


def application_filenames(language: str) -> tuple[str, str]:
    """Return deterministic candidate-based PDF names for an application language."""
    normalized = language.strip().casefold()
    if normalized.startswith(("de", "ger")):
        return "Candidate_Lebenslauf.pdf", "Candidate_Anschreiben.pdf"
    if normalized.startswith(("en", "eng")):
        return "Candidate_CV.pdf", "Candidate_Cover_Letter.pdf"
    raise ValueError("Application language must be English or German.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a job application folder.")
    parser.add_argument("output_root", type=Path)
    parser.add_argument("company")
    parser.add_argument("job_title")
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()

    folder = args.output_root / job_folder_name(args.company, args.job_title)
    drafts = folder / "drafts"
    if args.create:
        drafts.mkdir(parents=True, exist_ok=True)
    print(folder)
    print(drafts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
