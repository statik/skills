#!/usr/bin/env python3
"""
Check if eval logs show evidence of the skill being used.

Usage:
    python check_skill_usage.py [log_file.eval]

If no log file is specified, checks the most recent eval log.
"""

import json
import sys
import zipfile
from pathlib import Path


def check_log_for_skill_usage(log_file: Path) -> dict:
    """Check a single log file for skill usage indicators."""
    results = {
        "log_file": str(log_file),
        "task_name": log_file.stem.split("_")[3] if len(log_file.stem.split("_")) > 3 else "unknown",
        "samples_checked": 0,
        "skill_identifier_found": 0,
        "skill_markers_found": 0,
        "samples_with_markers": [],
    }

    skill_identifier = "DNS Troubleshooter Analysis"
    skill_markers = [
        "dig @",
        "doggo",
        "v=spf1",
        "permerror",
        "10-lookup",
    ]

    try:
        with zipfile.ZipFile(log_file, "r") as zf:
            # Get list of sample files
            sample_files = [f for f in zf.namelist() if f.startswith("samples/") and f.endswith(".json")]
            results["samples_checked"] = len(sample_files)

            for sample_file in sample_files:
                with zf.open(sample_file) as f:
                    data = json.load(f)

                    # Get the assistant's response
                    messages = data.get("messages", [])
                    if len(messages) < 2:
                        continue

                    response = messages[-1].get("content", "")

                    # Check for skill identifier
                    if skill_identifier in response:
                        results["skill_identifier_found"] += 1

                    # Check for skill markers
                    markers_in_response = [m for m in skill_markers if m.lower() in response.lower()]
                    if markers_in_response:
                        results["skill_markers_found"] += 1
                        results["samples_with_markers"].append({
                            "sample": sample_file,
                            "markers": markers_in_response,
                            "has_identifier": skill_identifier in response,
                            "response_length": len(response),
                        })

    except Exception as e:
        results["error"] = str(e)

    return results


def print_results(results: dict):
    """Print results in a readable format."""
    print("=" * 70)
    print("SKILL USAGE CHECK")
    print("=" * 70)
    print(f"\nLog file: {results['log_file']}")
    print(f"Task: {results['task_name']}")
    print(f"Samples checked: {results['samples_checked']}")

    if "error" in results:
        print(f"\n❌ Error: {results['error']}")
        return

    print(f"\n{'🔍 Skill Identifier Found:':<30} {results['skill_identifier_found']}/{results['samples_checked']}")
    print(f"{'Skill Markers Found:':<30} {results['skill_markers_found']}/{results['samples_checked']}")

    if results["skill_identifier_found"] > 0:
        print("\n✅ SKILL IS BEING USED!")
        print(f"   The skill identifier '🔍 DNS Troubleshooter Analysis' was found")
        print(f"   in {results['skill_identifier_found']} sample(s).")
    elif results["skill_markers_found"] > 0:
        print("\n⚠️  PARTIAL SKILL USAGE")
        print(f"   Skill markers were found but not the explicit identifier.")
        print(f"   This suggests skill knowledge is present but the format may not be followed.")
    else:
        print("\n❌ NO SKILL EVIDENCE FOUND")
        print("   Neither the skill identifier nor skill markers were detected.")
        print("   The skill may not be loaded or used.")

    if results["samples_with_markers"]:
        print(f"\n{'Sample Details:':<30}")
        for sample in results["samples_with_markers"][:3]:  # Show first 3
            identifier_status = "✓" if sample["has_identifier"] else "✗"
            print(f"  [{identifier_status}] {sample['sample']}")
            print(f"      Markers: {', '.join(sample['markers'])}")
            print(f"      Response: {sample['response_length']} chars")

        if len(results["samples_with_markers"]) > 3:
            print(f"  ... and {len(results['samples_with_markers']) - 3} more")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        log_file = Path(sys.argv[1])
    else:
        # Find most recent log file
        logs_dir = Path(__file__).parent / "logs"
        log_files = sorted(logs_dir.glob("*.eval"), key=lambda f: f.stat().st_mtime, reverse=True)

        if not log_files:
            print("❌ No eval logs found in logs/")
            print("\nRun an eval first:")
            print("  just test-claude-anthropic")
            print("  just test-copilot-anthropic")
            return 1

        log_file = log_files[0]

    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return 1

    results = check_log_for_skill_usage(log_file)
    print_results(results)

    # Return exit code based on results
    if "error" in results:
        return 1
    elif results["skill_identifier_found"] > 0:
        return 0  # Success - explicit skill usage
    elif results["skill_markers_found"] > 0:
        return 0  # Partial success - some evidence
    else:
        return 1  # No evidence of skill usage


if __name__ == "__main__":
    sys.exit(main())
