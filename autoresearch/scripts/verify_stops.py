#!/usr/bin/env python3
"""Verify that stop_conditions.json covers all safety bases."""

import json
import sys
import os


def verify(config_path: str = "stop_conditions.json") -> bool:
    if not os.path.exists(config_path):
        print(f"File not found: {config_path}")
        print("Run init.sh first, or create stop_conditions.json manually.")
        return False

    config = json.load(open(config_path))
    issues = []
    warnings = []

    # === Layer 1: Hard Limits (safety) ===
    hl = config.get("hard_limits", {})

    if "max_iterations" not in hl:
        issues.append("missing max_iterations (infinite loop risk)")
    elif hl["max_iterations"] > 200:
        warnings.append(f"max_iterations={hl['max_iterations']} — cost may be very high")

    if "max_runtime_minutes" not in hl:
        issues.append("missing max_runtime_minutes (unbounded time)")
    elif hl["max_runtime_minutes"] > 1440:
        warnings.append("max_runtime > 24h — review budget")

    if "max_cost_usd" not in hl:
        warnings.append("no max_cost_usd — no spending cap")

    # === Layer 2: Convergence ===
    conv = config.get("convergence", {})

    if "max_consecutive_failures" not in conv:
        issues.append("missing max_consecutive_failures (no plateau detection)")
    elif conv["max_consecutive_failures"] > 10:
        warnings.append("max_consecutive_failures > 10 — may waste budget on plateaus")

    if "target_score" not in conv:
        warnings.append("no target_score — loop won't know when 'good enough'")

    if "min_improvement_threshold" not in conv:
        warnings.append("no min_improvement_threshold — may keep trivial gains")

    # === Layer 3: Quality Gates ===
    qg = config.get("quality_gates", {})

    if not qg:
        warnings.append("no quality_gates section — no feature completeness checks")
    else:
        if "required_features" not in qg and "required_apis" not in qg:
            warnings.append("no required_features/required_apis — no completeness checklist")
        if "min_coverage_percent" not in qg:
            warnings.append("no min_coverage_percent")

    # === Cross-checks ===
    if "hard_limits" not in config:
        issues.append("entire hard_limits section missing")
    if "convergence" not in config:
        issues.append("entire convergence section missing")

    # === Report ===
    total_checks = 10
    passed = total_checks - len(issues) - len(warnings)

    print("=" * 50)
    print("  Stop Condition Completeness Report")
    print("=" * 50)

    if issues:
        print(f"\n  CRITICAL ({len(issues)}):")
        for item in issues:
            print(f"    [x] {item}")

    if warnings:
        print(f"\n  WARNING ({len(warnings)}):")
        for item in warnings:
            print(f"    [!] {item}")

    if not issues and not warnings:
        print("\n  All checks passed.")

    score = max(0, 1.0 - len(issues) * 0.2 - len(warnings) * 0.05)
    print(f"\n  Completeness: {score * 100:.0f}%")
    print(f"  Passed: {passed}/{total_checks}")
    print("=" * 50)

    return len(issues) == 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "stop_conditions.json"
    ok = verify(path)
    sys.exit(0 if ok else 1)
