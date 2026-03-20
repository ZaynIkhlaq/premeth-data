
"""Generate or update index.json files for each question folder."""

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def filename_to_name(filename_stem):
    """Convert a filename stem like '100_days_meth_enzymes' to a display name."""
    return " ".join(word.capitalize() for word in filename_stem.split("_"))


def generate_index_for_folder(folder):
    """Generate the index.json content for a folder. Returns (data, changed)."""
    question_files = sorted(f for f in folder.glob("*.json") if f.name != "index.json")

    papers = []
    for qfile in question_files:
        try:
            with open(qfile) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  WARNING: skipping {qfile.name}: {e}", file=sys.stderr)
            continue

        questions = data.get("questions", [])
        file_id = qfile.stem
        question_count = len(questions)

        # Determine subject: most common across questions
        subjects = Counter(q.get("subject") for q in questions if q.get("subject"))
        subject = subjects.most_common(1)[0][0] if subjects else ""

        # Collect unique topics in order of first appearance
        seen_topics = set()
        topics = []
        for q in questions:
            t = q.get("topic")
            if t and t not in seen_topics:
                seen_topics.add(t)
                topics.append(t)

        # Determine year: most common non-null year, or null
        years = Counter(q.get("year") for q in questions if q.get("year") is not None)
        year = years.most_common(1)[0][0] if years else None

        papers.append({
            "id": file_id,
            "name": filename_to_name(file_id),
            "subject": subject,
            "questionCount": question_count,
            "topics": sorted(topics),
            "year": year,
        })

    new_data = {"papers": papers}

    # Check if it differs from existing
    index_path = folder / "index.json"
    changed = True
    if index_path.exists():
        try:
            with open(index_path) as f:
                existing = json.load(f)
            changed = existing != new_data
        except (json.JSONDecodeError, OSError):
            changed = True

    return new_data, changed


def get_question_folders():
    folders = []
    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith(".") or entry.name in ("scripts", "node_modules", "__pycache__"):
            continue
        question_files = [f for f in entry.glob("*.json") if f.name != "index.json"]
        if question_files:
            folders.append(entry)
    return folders


def main():
    dry_run = "--dry-run" in sys.argv
    folders = get_question_folders()

    if not folders:
        print("No question folders found!")
        sys.exit(1)

    updated = 0
    unchanged = 0

    for folder in folders:
        data, changed = generate_index_for_folder(folder)

        if not changed:
            unchanged += 1
            continue

        if dry_run:
            print(f"  WOULD UPDATE: {folder.name}/index.json")
        else:
            index_path = folder / "index.json"
            with open(index_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"  Updated: {folder.name}/index.json")

        updated += 1

    action = "would update" if dry_run else "updated"
    print(f"\nDone: {action} {updated}, unchanged {unchanged} (total {len(folders)} folders)")


if __name__ == "__main__":
    main()
