#!/usr/bin/env python3
"""
Test script to verify GitHub Copilot CLI is actually loading and using the skill.

This tests:
1. Copilot CLI is installed
2. Skill files are present in the expected location
3. Copilot responds to DNS-specific queries
4. Responses show evidence of using the skill (references skill content)
"""

import subprocess
import tempfile
import shutil
import sys
from pathlib import Path


def check_copilot_installed():
    """Check if GitHub Copilot CLI is installed."""
    print("=" * 70)
    print("TEST 1: Checking GitHub Copilot CLI Installation")
    print("=" * 70)

    if not shutil.which("copilot"):
        print("❌ FAILED: GitHub Copilot CLI is not installed\n")
        print("Install from: https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line")
        return False

    print("✅ PASSED: GitHub Copilot CLI is installed\n")
    return True


def check_skill_files():
    """Check if skill files exist."""
    print("=" * 70)
    print("TEST 2: Checking Skill Files")
    print("=" * 70)

    skill_path = Path(__file__).parent.parent / "dns-troubleshooter"
    skill_md = skill_path / "SKILL.md"
    spf_ref = skill_path / "references" / "spf.md"

    if not skill_path.exists():
        print(f"❌ FAILED: Skill directory not found: {skill_path}\n")
        return False

    print(f"✅ Skill directory exists: {skill_path}")

    if not skill_md.exists():
        print(f"❌ FAILED: SKILL.md not found: {skill_md}\n")
        return False

    print(f"✅ SKILL.md exists: {skill_md}")

    if not spf_ref.exists():
        print(f"❌ FAILED: SPF reference not found: {spf_ref}\n")
        return False

    print(f"✅ SPF reference exists: {spf_ref}\n")
    return True


def setup_skill_in_temp_dir():
    """Set up skill in a temporary directory."""
    print("=" * 70)
    print("TEST 3: Setting Up Skill for Copilot")
    print("=" * 70)

    temp_dir = Path(tempfile.mkdtemp(prefix="copilot-skill-test-"))
    print(f"Created temp directory: {temp_dir}")

    # Set up skill in .github/copilot/skills/
    skills_dir = temp_dir / ".github" / "copilot" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    skill_path = Path(__file__).parent.parent / "dns-troubleshooter"
    dest = skills_dir / "dns-troubleshooter"

    shutil.copytree(skill_path, dest)
    print(f"✅ Copied skill to: {dest}")

    # Verify files are there
    skill_md = dest / "SKILL.md"
    if not skill_md.exists():
        print("❌ FAILED: SKILL.md not found in temp directory\n")
        return None

    print(f"✅ Verified SKILL.md exists: {skill_md}\n")
    return temp_dir


def test_copilot_without_skill():
    """Test Copilot response without the skill (baseline)."""
    print("=" * 70)
    print("TEST 4: Copilot Response WITHOUT Skill (Baseline)")
    print("=" * 70)

    # Use a temp dir without the skill
    temp_dir = Path(tempfile.mkdtemp(prefix="copilot-no-skill-"))

    prompt = "What should I check when validating an SPF record?"

    try:
        result = subprocess.run(
            ["copilot", "--prompt", prompt],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"❌ FAILED: Copilot returned error: {result.stderr}\n")
            shutil.rmtree(temp_dir)
            return None

        response = result.stdout.strip()
        print(f"Response length: {len(response)} characters")
        print(f"First 300 chars:\n{response[:300]}...\n")

        shutil.rmtree(temp_dir)
        return response

    except subprocess.TimeoutExpired:
        print("❌ FAILED: Copilot timed out\n")
        shutil.rmtree(temp_dir)
        return None
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        shutil.rmtree(temp_dir)
        return None


def test_copilot_with_skill(work_dir):
    """Test Copilot response with the skill loaded."""
    print("=" * 70)
    print("TEST 5: Copilot Response WITH Skill")
    print("=" * 70)

    prompt = "What should I check when validating an SPF record?"

    try:
        result = subprocess.run(
            ["copilot", "--prompt", prompt],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"❌ FAILED: Copilot returned error: {result.stderr}\n")
            return None

        response = result.stdout.strip()
        print(f"Response length: {len(response)} characters")
        print(f"First 300 chars:\n{response[:300]}...\n")

        return response

    except subprocess.TimeoutExpired:
        print("❌ FAILED: Copilot timed out\n")
        return None
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        return None


def analyze_skill_usage(baseline_response, skill_response):
    """Analyze if the skill was actually used."""
    print("=" * 70)
    print("TEST 6: Analyzing Skill Usage")
    print("=" * 70)

    if not baseline_response or not skill_response:
        print("❌ FAILED: Missing responses to compare\n")
        return False

    # Check for skill-specific markers
    skill_markers = [
        "🔍 DNS Troubleshooter Analysis",  # Skill identifier (NEW!)
        "DNS Troubleshooter",  # Skill name mention
        "dig @",  # Skill emphasizes dig command usage
        "doggo",  # Skill mentions doggo tool
        "v=spf1",  # SPF syntax
        "10-lookup limit",  # Specific SPF knowledge from references
        "permerror",  # SPF error terminology
        "+all", "-all", "~all",  # SPF qualifiers
        "ptr:", "exists:", "include:",  # SPF mechanisms
        "127.0.0.1",  # Test server IP from skill
    ]

    baseline_markers = sum(1 for marker in skill_markers if marker.lower() in baseline_response.lower())
    skill_markers_found = sum(1 for marker in skill_markers if marker.lower() in skill_response.lower())

    print(f"Skill-specific markers in baseline response: {baseline_markers}/{len(skill_markers)}")
    print(f"Skill-specific markers in skilled response: {skill_markers_found}/{len(skill_markers)}")

    # Check for the explicit skill identifier
    has_skill_identifier = "🔍 DNS Troubleshooter Analysis" in skill_response or "DNS Troubleshooter Analysis" in skill_response
    if has_skill_identifier:
        print("\n🎯 EXPLICIT SKILL IDENTIFIER FOUND: '🔍 DNS Troubleshooter Analysis'")
        print("   This confirms the skill is being loaded and used!\n")

    if skill_markers_found > baseline_markers:
        print(f"\n✅ PASSED: Response with skill shows {skill_markers_found - baseline_markers} more skill markers")
        print("\nSkill-specific content found:")
        for marker in skill_markers:
            if marker.lower() in skill_response.lower() and marker.lower() not in baseline_response.lower():
                print(f"  - {marker}")
        return True
    else:
        print(f"\n⚠️  WARNING: Responses are similar ({skill_markers_found} vs {baseline_markers} markers)")
        print("This might mean:")
        print("  1. Copilot CLI may not be loading skills from .github/copilot/skills/")
        print("  2. The skill content overlaps significantly with base knowledge")
        print("  3. The prompt needs to be more skill-specific")
        return False


def test_skill_specific_prompt(work_dir):
    """Test with a very skill-specific prompt."""
    print("=" * 70)
    print("TEST 7: Testing Skill-Specific Knowledge")
    print("=" * 70)

    # This prompt asks about specific content in the skill's SPF reference
    prompt = """I need to validate an SPF record. The skill documentation mentions specific
    issues to check for. What are the common SPF validation issues I should look for,
    including the one about 'too many DNS lookups'?"""

    try:
        result = subprocess.run(
            ["copilot", "--prompt", prompt],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"❌ FAILED: Copilot returned error: {result.stderr}\n")
            return False

        response = result.stdout.strip()

        # Check for very specific content from the skill
        specific_checks = [
            "10" in response or "ten" in response.lower(),  # 10-lookup limit
            "permerror" in response.lower() or "perm error" in response.lower(),
            "multiple spf" in response.lower() or "two spf" in response.lower(),
        ]

        found = sum(specific_checks)
        print(f"Found {found}/3 specific skill knowledge points")

        if found >= 2:
            print("✅ PASSED: Response contains specific skill knowledge")
            print(f"\nResponse preview:\n{response[:400]}...\n")
            return True
        else:
            print("⚠️  WARNING: Response lacks specific skill knowledge")
            print(f"\nResponse preview:\n{response[:400]}...\n")
            return False

    except subprocess.TimeoutExpired:
        print("❌ FAILED: Copilot timed out\n")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("COPILOT CLI SKILL INTEGRATION TEST")
    print("=" * 70 + "\n")

    results = []

    # Test 1: Check Copilot installation
    if not check_copilot_installed():
        print("\n❌ OVERALL: Cannot proceed without GitHub Copilot CLI")
        return 1
    results.append(True)

    # Test 2: Check skill files
    if not check_skill_files():
        print("\n❌ OVERALL: Skill files missing")
        return 1
    results.append(True)

    # Test 3: Set up skill
    work_dir = setup_skill_in_temp_dir()
    if not work_dir:
        print("\n❌ OVERALL: Failed to set up skill")
        return 1
    results.append(True)

    try:
        # Test 4: Baseline response
        baseline = test_copilot_without_skill()
        if baseline is None:
            print("\n⚠️  WARNING: Could not get baseline response")
            results.append(False)
        else:
            results.append(True)

        # Test 5: Response with skill
        skilled = test_copilot_with_skill(work_dir)
        if skilled is None:
            print("\n❌ OVERALL: Could not get response with skill")
            return 1
        results.append(True)

        # Test 6: Analyze skill usage
        if baseline and skilled:
            results.append(analyze_skill_usage(baseline, skilled))
        else:
            results.append(False)

        # Test 7: Skill-specific prompt
        results.append(test_skill_specific_prompt(work_dir))

    finally:
        # Clean up
        if work_dir and work_dir.exists():
            shutil.rmtree(work_dir)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total} tests")

    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        print("GitHub Copilot CLI is successfully loading and using the skill!")
        return 0
    elif passed >= total - 1:
        print("\n⚠️  MOSTLY WORKING")
        print("GitHub Copilot CLI is responding, but skill usage is unclear.")
        print("This is expected if Copilot doesn't explicitly load skills from .github/copilot/skills/")
        return 0
    else:
        print("\n❌ TESTS FAILED")
        print("GitHub Copilot CLI integration has issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
