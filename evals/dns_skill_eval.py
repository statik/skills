"""
InspectAI eval for dns-troubleshooter skill.

Tests the skill's ability to diagnose DNS issues using a local test DNS server.
"""

import os
import re
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, MemoryDataset
from inspect_ai.scorer import scorer, accuracy, stderr, Score, CORRECT, INCORRECT
from inspect_ai.solver import generate, system_message

from dns_server import TestDNSServer
from test_zones import get_all_zones, SCENARIOS, TEST_DOMAIN

# Valid diagnosis values the model should output
VALID_DIAGNOSES = {"valid", "invalid", "warning", "insecure", "incomplete"}


@scorer(metrics=[accuracy(), stderr()])
def diagnosis_match():
    """Score by matching the diagnosis keyword in the model's response.

    Extracts the diagnosis from the model output and compares it to the
    expected_diagnosis in sample metadata. No model grading required.
    """

    async def score(state, target):
        # Get expected diagnosis from metadata
        expected = state.metadata.get("expected_diagnosis", "").lower()

        # Extract diagnosis from model output
        completion = state.output.completion.lower()

        # Look for explicit diagnosis patterns
        patterns = [
            r"diagnos(?:is|ed?\s+as)[:\s]+(\w+)",
            r"status[:\s]+(\w+)",
            r"conclusion[:\s]+(\w+)",
        ]

        found_diagnosis = None
        for pattern in patterns:
            match = re.search(pattern, completion)
            if match and match.group(1) in VALID_DIAGNOSES:
                found_diagnosis = match.group(1)
                break

        # Fallback: check if any diagnosis keyword appears prominently
        if not found_diagnosis:
            for diag in VALID_DIAGNOSES:
                if diag in completion:
                    found_diagnosis = diag
                    break

        is_correct = found_diagnosis == expected

        return Score(
            value=CORRECT if is_correct else INCORRECT,
            answer=found_diagnosis or "not found",
            explanation=f"Expected: {expected}, Found: {found_diagnosis}"
        )

    return score


# Port for the test DNS server
DNS_PORT = int(os.environ.get("DNS_TEST_PORT", "5053"))

# Path to the skill
SKILL_PATH = Path(__file__).parent.parent / "dns-troubleshooter"


def get_skill_content() -> str:
    """Load the dns-troubleshooter skill content."""
    skill_md = SKILL_PATH / "SKILL.md"
    if skill_md.exists():
        return skill_md.read_text()
    return ""


def make_system_prompt() -> str:
    """Create system prompt with skill instructions."""
    skill_content = get_skill_content()

    return f"""You are a DNS troubleshooting expert. You have access to DNS diagnostic tools.

IMPORTANT: For all DNS queries in this evaluation, use the test DNS server at 127.0.0.1 port {DNS_PORT}.
Use dig with: dig @127.0.0.1 -p {DNS_PORT} <domain> <record_type>
Or with doggo: doggo <domain> @127.0.0.1:{DNS_PORT}

{skill_content}

When analyzing DNS records, provide:
1. Your finding
2. The command you used to verify
3. Your diagnosis (valid, invalid, warning, insecure, incomplete)
4. Explanation of the issue if any
"""


def create_spf_samples() -> list[Sample]:
    """Create evaluation samples for SPF scenarios."""
    samples = []

    for scenario_id, scenario in SCENARIOS.items():
        if scenario["category"] != "spf":
            continue

        domain = scenario["zone"]
        expected = scenario["expected_diagnosis"]
        description = scenario["description"]

        samples.append(
            Sample(
                input=f"Analyze the SPF record for {domain} and determine if it is properly configured. What issues, if any, exist?",
                target=f"The SPF record should be diagnosed as: {expected}. {description}",
                metadata={
                    "scenario_id": scenario_id,
                    "category": "spf",
                    "expected_diagnosis": expected,
                },
            )
        )

    return samples


def create_conflict_samples() -> list[Sample]:
    """Create evaluation samples for record conflict scenarios."""
    samples = []

    for scenario_id, scenario in SCENARIOS.items():
        if scenario["category"] != "conflict":
            continue

        domain = scenario["zone"]
        expected = scenario["expected_diagnosis"]
        description = scenario["description"]

        samples.append(
            Sample(
                input=f"Check the DNS records for {domain} for any conflicts or misconfigurations. Are there any issues?",
                target=f"The configuration should be diagnosed as: {expected}. {description}",
                metadata={
                    "scenario_id": scenario_id,
                    "category": "conflict",
                    "expected_diagnosis": expected,
                },
            )
        )

    return samples


def create_all_samples() -> list[Sample]:
    """Create all evaluation samples."""
    samples = []
    samples.extend(create_spf_samples())
    samples.extend(create_conflict_samples())
    return samples


# Global server instance for the eval
_server: TestDNSServer | None = None


def start_dns_server():
    """Start the test DNS server."""
    global _server
    if _server is None:
        zones = get_all_zones()
        _server = TestDNSServer(zones, port=DNS_PORT)
        _server.start()


def stop_dns_server():
    """Stop the test DNS server."""
    global _server
    if _server is not None:
        _server.stop()
        _server = None


@task
def dns_troubleshooter_eval() -> Task:
    """Main evaluation task for dns-troubleshooter skill."""
    # Start the DNS server
    start_dns_server()

    samples = create_all_samples()
    dataset = MemoryDataset(samples=samples, name="dns-troubleshooter-eval")

    return Task(
        dataset=dataset,
        solver=[
            system_message(make_system_prompt()),
            generate(),
        ],
        scorer=diagnosis_match(),
    )


@task
def dns_spf_eval() -> Task:
    """SPF-focused evaluation task."""
    start_dns_server()

    samples = create_spf_samples()
    dataset = MemoryDataset(samples=samples, name="dns-spf-eval")

    return Task(
        dataset=dataset,
        solver=[
            system_message(make_system_prompt()),
            generate(),
        ],
        scorer=diagnosis_match(),
    )


@task
def dns_conflict_eval() -> Task:
    """Record conflict evaluation task."""
    start_dns_server()

    samples = create_conflict_samples()
    dataset = MemoryDataset(samples=samples, name="dns-conflict-eval")

    return Task(
        dataset=dataset,
        solver=[
            system_message(make_system_prompt()),
            generate(),
        ],
        scorer=diagnosis_match(),
    )


if __name__ == "__main__":
    # Quick test of the DNS server
    print(f"Starting DNS server on port {DNS_PORT}...")
    start_dns_server()
    print(f"Test with: dig @127.0.0.1 -p {DNS_PORT} spf-valid.{TEST_DOMAIN} TXT")
    print(f"Test with: dig @127.0.0.1 -p {DNS_PORT} spf-multiple.{TEST_DOMAIN} TXT")
    print("Press Ctrl+C to stop")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_dns_server()
        print("Server stopped.")
