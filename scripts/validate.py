
"""Validate question JSON files and index.json files in the premeth-data repo."""

import json
import os
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


REQUIRED_QUESTION_FIELDS = {
    "text": str,
    "subject": str,
    "topic": str,
    "options": list,
    "explanation": str,
}
OPTIONAL_QUESTION_FIELDS = {
    "image": (str, type(None)),
    "explanationImage": (str, type(None)),
    "hints": list,
    "year": (int, type(None)),
}
ALL_QUESTION_FIELDS = set(REQUIRED_QUESTION_FIELDS) | set(OPTIONAL_QUESTION_FIELDS)

REQUIRED_OPTION_FIELDS = {
    "letter": str,
    "text": str,
    "isCorrect": bool,
}
OPTIONAL_OPTION_FIELDS = {
    "explanation": str,
}
ALL_OPTION_FIELDS = set(REQUIRED_OPTION_FIELDS) | set(OPTIONAL_OPTION_FIELDS)


REQUIRED_PAPER_FIELDS = {
    "id": str,
    "name": str,
    "subject": str,
    "questionCount": int,
    "topics": list,
}
OPTIONAL_PAPER_FIELDS = {
    "year": (int, type(None)),
}
ALL_PAPER_FIELDS = set(REQUIRED_PAPER_FIELDS) | set(OPTIONAL_PAPER_FIELDS)


def validate_option(option, q_idx, opt_idx, filepath, errors):
    prefix = f"{filepath}: question[{q_idx}] option[{opt_idx}]"

    if not isinstance(option, dict):
        errors.append(f"{prefix}: expected object, got {type(option).__name__}")
        return

    for field, expected_type in REQUIRED_OPTION_FIELDS.items():
        if field not in option:
            errors.append(f"{prefix}: missing required field '{field}'")
        elif not isinstance(option[field], expected_type):
            errors.append(f"{prefix}: '{field}' should be {expected_type.__name__}, got {type(option[field]).__name__}")

    for field, expected_type in OPTIONAL_OPTION_FIELDS.items():
        if field in option and not isinstance(option[field], expected_type):
            errors.append(f"{prefix}: '{field}' should be {expected_type.__name__}, got {type(option[field]).__name__}")

    extra = set(option.keys()) - ALL_OPTION_FIELDS
    if extra:
        errors.append(f"{prefix}: unexpected fields {extra}")


def validate_question(question, q_idx, filepath, errors):
    prefix = f"{filepath}: question[{q_idx}]"

    if not isinstance(question, dict):
        errors.append(f"{prefix}: expected object, got {type(question).__name__}")
        return

    # Required fields
    for field, expected_type in REQUIRED_QUESTION_FIELDS.items():
        if field not in question:
            errors.append(f"{prefix}: missing required field '{field}'")
        elif not isinstance(question[field], expected_type):
            errors.append(f"{prefix}: '{field}' should be {expected_type.__name__}, got {type(question[field]).__name__}")

    # Optional fields type check
    for field, expected_types in OPTIONAL_QUESTION_FIELDS.items():
        if field in question and not isinstance(question[field], expected_types):
            errors.append(f"{prefix}: '{field}' has wrong type {type(question[field]).__name__}")

    # Extra fields
    extra = set(question.keys()) - ALL_QUESTION_FIELDS
    if extra:
        errors.append(f"{prefix}: unexpected fields {extra}")

    # Non-empty text
    if isinstance(question.get("text"), str) and not question["text"].strip():
        errors.append(f"{prefix}: 'text' is empty")

    # Options validation
    options = question.get("options")
    if isinstance(options, list):
        for i, opt in enumerate(options):
            validate_option(opt, q_idx, i, filepath, errors)

        # Exactly one correct answer
        correct_count = sum(1 for o in options if isinstance(o, dict) and o.get("isCorrect") is True)
        if correct_count == 0:
            errors.append(f"{prefix}: no option has isCorrect=true")
        elif correct_count > 1:
            errors.append(f"{prefix}: {correct_count} options have isCorrect=true (expected 1)")

        # No empty option text
        for i, opt in enumerate(options):
            if isinstance(opt, dict) and isinstance(opt.get("text"), str) and not opt["text"].strip():
                errors.append(f"{prefix}: option[{i}] has empty 'text'")


def validate_question_file(filepath, errors):
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"{filepath}: invalid JSON: {e}")
        return None

    if not isinstance(data, dict):
        errors.append(f"{filepath}: root should be an object")
        return None

    if "questions" not in data:
        errors.append(f"{filepath}: missing 'questions' array")
        return None

    extra_root = set(data.keys()) - {"questions"}
    if extra_root:
        errors.append(f"{filepath}: unexpected root fields {extra_root}")

    questions = data["questions"]
    if not isinstance(questions, list):
        errors.append(f"{filepath}: 'questions' should be an array")
        return None

    for i, q in enumerate(questions):
        validate_question(q, i, filepath, errors)

    return data


def validate_index(folder_path, errors):
    index_path = folder_path / "index.json"
    if not index_path.exists():
        errors.append(f"{folder_path}: missing index.json")
        return

    try:
        with open(index_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"{index_path}: invalid JSON: {e}")
        return

    if not isinstance(data, dict) or "papers" not in data:
        errors.append(f"{index_path}: missing 'papers' array")
        return

    papers = data["papers"]
    if not isinstance(papers, list):
        errors.append(f"{index_path}: 'papers' should be an array")
        return

    # Collect actual question files in this folder
    actual_files = {f.stem for f in folder_path.glob("*.json") if f.name != "index.json"}
    indexed_ids = set()

    for i, paper in enumerate(papers):
        prefix = f"{index_path}: papers[{i}]"

        if not isinstance(paper, dict):
            errors.append(f"{prefix}: expected object")
            continue

        # Required fields
        for field, expected_type in REQUIRED_PAPER_FIELDS.items():
            if field not in paper:
                errors.append(f"{prefix}: missing required field '{field}'")
            elif not isinstance(paper[field], expected_type):
                errors.append(f"{prefix}: '{field}' should be {expected_type.__name__}")

        # Optional fields
        for field, expected_types in OPTIONAL_PAPER_FIELDS.items():
            if field in paper and not isinstance(paper[field], expected_types):
                errors.append(f"{prefix}: '{field}' has wrong type")

        # Extra fields
        extra = set(paper.keys()) - ALL_PAPER_FIELDS
        if extra:
            errors.append(f"{prefix}: unexpected fields {extra}")

        paper_id = paper.get("id")
        if isinstance(paper_id, str):
            indexed_ids.add(paper_id)

            # Check corresponding file exists
            if paper_id not in actual_files:
                errors.append(f"{prefix}: id '{paper_id}' has no matching .json file")
            else:
                # Validate questionCount
                qfile = folder_path / f"{paper_id}.json"
                try:
                    with open(qfile) as f:
                        qdata = json.load(f)
                    actual_count = len(qdata.get("questions", []))
                    expected_count = paper.get("questionCount")
                    if isinstance(expected_count, int) and actual_count != expected_count:
                        errors.append(
                            f"{prefix}: questionCount is {expected_count} but "
                            f"{paper_id}.json has {actual_count} questions"
                        )
                except (json.JSONDecodeError, OSError):
                    pass  # Already caught by question file validation

    # Files not in index
    missing_from_index = actual_files - indexed_ids
    for m in sorted(missing_from_index):
        errors.append(f"{index_path}: file '{m}.json' exists but is not in index")


def get_question_folders():
    """Return folders that contain question JSON files (exclude hidden dirs, scripts, etc.)."""
    folders = []
    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith(".") or entry.name in ("scripts", "node_modules", "__pycache__"):
            continue
        # Must contain at least one .json file that isn't index.json
        question_files = [f for f in entry.glob("*.json") if f.name != "index.json"]
        if question_files:
            folders.append(entry)
    return folders


def main():
    errors = []
    folders = get_question_folders()

    if not folders:
        print("No question folders found!")
        sys.exit(1)

    total_files = 0
    for folder in folders:
        # Validate index.json
        validate_index(folder, errors)

        # Validate each question file
        for qfile in sorted(folder.glob("*.json")):
            if qfile.name == "index.json":
                continue
            total_files += 1
            validate_question_file(qfile, errors)

    if errors:
        print(f"VALIDATION FAILED: {len(errors)} error(s) found\n")
        for err in errors:
            # Make paths relative for readability
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"All checks passed! Validated {total_files} question files across {len(folders)} folders.")
        sys.exit(0)


if __name__ == "__main__":
    main()
