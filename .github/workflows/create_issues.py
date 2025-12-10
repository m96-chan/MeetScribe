#!/usr/bin/env python3
"""
Create GitHub Issues from JSON files in ZIP archives.
"""

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def create_issue_body(data):
    """Create issue body from JSON data."""
    lines = ["## Overview", "", data.get("overview", ""), ""]

    lines.extend(
        [
            "## Details",
            "",
            f"- **Layer**: {data.get('layer', '')}",
            f"- **Directory**: `{data.get('directory', '')}`",
            f"- **Priority**: {data.get('priority', '')}",
            "",
            "## Tasks",
            "",
        ]
    )

    for task in data.get("tasks", []):
        lines.append(f"- {task}")

    if data.get("acceptance_criteria"):
        lines.extend(["", "## Acceptance Criteria", ""])
        for criteria in data["acceptance_criteria"]:
            lines.append(f"- {criteria}")

    if data.get("related_files"):
        lines.extend(["", "## Related Files", ""])
        for file in data["related_files"]:
            lines.append(f"- `{file}`")

    lines.extend(["", "---", "", "*Auto-generated issue*"])

    return "\n".join(lines)


def ensure_label_exists(label, repo):
    """Create label if it doesn't exist."""
    # Check if label exists
    result = subprocess.run(
        ["gh", "label", "list", "--repo", repo, "--json", "name"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        import json

        existing_labels = json.loads(result.stdout)
        label_names = [l["name"] for l in existing_labels]

        if label not in label_names:
            # Create label with default color
            subprocess.run(
                ["gh", "label", "create", label, "--repo", repo, "--color", "ededed"],
                capture_output=True,
                text=True,
                check=False,
            )


def create_issue(title, body, labels, repo):
    """Create GitHub issue using gh CLI."""
    # Ensure all labels exist first
    for label in labels:
        ensure_label_exists(label, repo)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
        f.write(body)
        body_file = f.name

    try:
        cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body-file", body_file]

        for label in labels:
            cmd.extend(["--label", label])

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            error_msg = f"gh CLI failed (exit {result.returncode})"
            if result.stderr:
                error_msg += f": {result.stderr.strip()}"
            raise RuntimeError(error_msg)

        return result.stdout.strip()
    finally:
        os.unlink(body_file)


def process_zip(zip_path, repo):
    """Process a ZIP file containing JSON issue definitions."""
    print(f"Processing: {zip_path.name}")

    issues_created = 0
    issues_failed = 0

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_dir)

        json_files = sorted(Path(temp_dir).glob("*.json"))

        for json_file in json_files:
            print(f"  - {json_file.name}")

            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)

                title = data.get("title", "Untitled Issue")
                body = create_issue_body(data)
                labels = data.get("labels", [])

                issue_url = create_issue(title, body, labels, repo)
                print(f"    ✓ Created: {issue_url}")
                issues_created += 1

            except Exception as e:
                print(f"    ✗ Failed: {e}")
                issues_failed += 1
                # Continue processing other issues

    print(f"  Summary: {issues_created} created, {issues_failed} failed")
    return issues_created


def main():
    issues_dir = Path(".github/issues")

    if not issues_dir.exists():
        print("No .github/issues directory found")
        return

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        print("ERROR: GITHUB_REPOSITORY not set")
        sys.exit(1)

    zip_files = list(issues_dir.glob("*.zip"))

    if not zip_files:
        print("No ZIP files found")
        return

    total_issues = 0
    processed_dir = issues_dir / "processed"
    processed_dir.mkdir(exist_ok=True)

    for zip_file in zip_files:
        issues_created = process_zip(zip_file, repo)
        total_issues += issues_created

        # Move to processed
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = processed_dir / f"{timestamp}_{zip_file.name}"
        zip_file.rename(new_name)
        print(f"  Archived: {new_name.name}")

    print(f"\nTotal issues created: {total_issues}")


if __name__ == "__main__":
    main()
