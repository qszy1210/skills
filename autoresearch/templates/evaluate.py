#!/usr/bin/env python3
"""
AutoResearch Evaluation Script Template

Customize this for your project. Requirements:
  - Print a single integer score to stdout (for the loop script to read)
  - Print detailed breakdown to stderr (for the agent to analyze)
  - Be fully automated — no human input needed
  - Return 0 exit code even if score is low

Scoring guide:
  - Total should add up to 100 (easy to reason about)
  - Use multiple orthogonal dimensions (avoid Goodhart's Law)
  - Weight dimensions by importance to your project
"""

import subprocess
import json
import os
import sys


# ━━━ Configuration ━━━
# Change these for your project:

PROJECT_MODULE = "my_project"       # Python import name or source dir
TEST_COMMAND = ["python", "-m", "pytest", "-q"]
SOURCE_DIR = "src/"                 # Where source code lives


# ━━━ Dimension Checkers ━━━

def check_compiles() -> tuple[bool, int]:
    """Can the project be imported/compiled? (10 points)"""
    MAX = 10
    result = subprocess.run(
        ["python", "-c", f"import {PROJECT_MODULE}"],
        capture_output=True
    )
    ok = result.returncode == 0
    return ok, MAX if ok else 0


def check_tests() -> tuple[dict, int]:
    """Do tests pass? (30 points)"""
    MAX = 30
    result = subprocess.run(
        TEST_COMMAND + ["--tb=line"],
        capture_output=True, text=True
    )

    passed = failed = 0
    for line in result.stdout.split("\n"):
        if "passed" in line:
            for word in line.split():
                if word.isdigit():
                    passed = int(word)
                    break
        if "failed" in line:
            for word in line.split():
                if word.isdigit():
                    failed = int(word)
                    break

    total = passed + failed
    if total == 0:
        return {"passed": 0, "failed": 0, "total": 0}, 0

    score = int(passed / total * MAX)
    return {"passed": passed, "failed": failed, "total": total}, score


def check_coverage() -> tuple[float, int]:
    """Test coverage percentage. (20 points)"""
    MAX = 20
    result = subprocess.run(
        TEST_COMMAND + [f"--cov={PROJECT_MODULE}", "--cov-report=json", "--cov-report=term"],
        capture_output=True, text=True
    )

    if os.path.exists("coverage.json"):
        try:
            cov = json.load(open("coverage.json"))
            pct = cov["totals"]["percent_covered"]
            score = min(int(pct / 100 * MAX), MAX)
            return pct, score
        except (KeyError, json.JSONDecodeError):
            pass

    return 0.0, 0


def check_feature_completeness() -> tuple[list, list, int]:
    """Are required features/APIs implemented? (25 points)"""
    MAX = 25

    # ━━━ CUSTOMIZE THIS LIST ━━━
    required_features = [
        # ("function_or_class_name", "description"),
        # Examples:
        # ("connect", "Connect to server"),
        # ("disconnect", "Disconnect from server"),
        # ("send_message", "Send a message"),
    ]

    if not required_features:
        return [], [], MAX  # No checklist = full marks (define yours!)

    implemented = []
    missing = []
    for name, desc in required_features:
        result = subprocess.run(
            ["grep", "-r", f"def {name}", SOURCE_DIR],
            capture_output=True
        )
        if result.returncode == 0:
            implemented.append(name)
        else:
            missing.append(name)

    total = len(required_features)
    score = int(len(implemented) / total * MAX) if total > 0 else 0
    return implemented, missing, score


def check_error_handling() -> int:
    """Does the code handle errors properly? (10 points)"""
    MAX = 10
    patterns = ["try:", "except ", "raise ", "logging.error", "logger.error"]
    found = 0

    for pattern in patterns:
        result = subprocess.run(
            ["grep", "-r", pattern, SOURCE_DIR],
            capture_output=True
        )
        if result.returncode == 0:
            found += 1

    return min(found * 2, MAX)


def check_type_safety() -> int:
    """Type annotations and documentation. (5 points)"""
    MAX = 5
    score = 0

    result = subprocess.run(
        ["grep", "-rE", r"def .+\(.+:.+\)", SOURCE_DIR],
        capture_output=True, text=True
    )
    typed = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    score += min(typed, 3)

    result = subprocess.run(
        ["grep", "-r", '"""', SOURCE_DIR],
        capture_output=True, text=True
    )
    docs = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    score += min(docs // 3, 2)

    return min(score, MAX)


# ━━━ Main ━━━

def main():
    results = {}

    compiles, c_score = check_compiles()
    results["compilation"] = {"pass": compiles, "score": c_score, "max": 10}

    test_info, t_score = check_tests()
    results["tests"] = {**test_info, "score": t_score, "max": 30}

    cov_pct, cov_score = check_coverage()
    results["coverage"] = {"percent": round(cov_pct, 1), "score": cov_score, "max": 20}

    impl, miss, feat_score = check_feature_completeness()
    results["features"] = {
        "implemented": impl, "missing": miss,
        "score": feat_score, "max": 25
    }

    err_score = check_error_handling()
    results["error_handling"] = {"score": err_score, "max": 10}

    type_score = check_type_safety()
    results["type_safety"] = {"score": type_score, "max": 5}

    total = sum(r["score"] for r in results.values())
    max_total = sum(r["max"] for r in results.values())
    results["_summary"] = {"total": total, "max": max_total}

    # Detailed report to stderr (agent reads this)
    print(json.dumps(results, indent=2, ensure_ascii=False), file=sys.stderr)

    # Score to stdout (loop script reads this)
    print(total)


if __name__ == "__main__":
    main()
