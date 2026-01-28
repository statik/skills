"""
InspectAI eval for dns-troubleshooter skill.

Tests the skill by running Claude Code CLI with the skill installed,
using a local test DNS server for queries.

Implements eval best practices from:
https://developers.openai.com/blog/eval-skills/

Measures:
- Outcome goals: Correct diagnosis (model_graded_fact)
- Process goals: Did Claude use doggo/dig? Query the right server?
- Style goals: Proper output format
- Efficiency goals: Minimal commands
"""

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, MemoryDataset
from inspect_ai.model import ModelOutput, ChatMessageAssistant
from inspect_ai.scorer import model_graded_fact
from inspect_ai.solver import Solver, TaskState, solver

from dns_server import TestDNSServer
from test_zones import get_all_zones, SCENARIOS, TEST_DOMAIN, NEGATIVE_SCENARIOS
from scorers import (
    dns_tool_used,
    doggo_preferred,
    test_server_queried,
    correct_domain_queried,
    command_efficiency,
    output_format_check,
    skill_not_triggered,
)

# Port for the test DNS server
DNS_PORT = int(os.environ.get("DNS_TEST_PORT", "5053"))

# Path to the skill
SKILL_PATH = Path(__file__).parent.parent / "dns-troubleshooter"

# Timeout for Claude Code execution (seconds)
CLAUDE_TIMEOUT = 120

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


def setup_skill_directory(work_dir: Path) -> None:
    """Set up the skill in the working directory's .claude/skills folder."""
    skills_dir = work_dir / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Copy the skill to the working directory
    dest = skills_dir / "dns-troubleshooter"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SKILL_PATH, dest)


@dataclass
class ClaudeCodeResult:
    """Result from running Claude Code CLI."""
    response: str  # Final assistant response text
    trace: Any  # Full JSON trace for analysis
    commands: list[dict]  # Extracted command executions
    success: bool  # Whether execution succeeded


def extract_commands_from_output(trace: Any) -> list[dict]:
    """Extract command executions from Claude Code JSON trace."""
    commands = []

    if trace is None:
        return commands

    # Handle list format (array of messages)
    messages = trace if isinstance(trace, list) else trace.get("messages", [])

    for msg in messages:
        if msg.get("type") == "assistant":
            content = msg.get("content", [])
            for block in content:
                if block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    tool_input = block.get("input", {})

                    # Check for bash/command execution tools
                    if tool_name.lower() in ("bash", "execute", "run", "shell"):
                        command = tool_input.get("command", "")
                        commands.append({
                            "tool": tool_name,
                            "command": command,
                            "input": tool_input,
                        })

    return commands


def run_claude_code(prompt: str, work_dir: Path, model: str | None = None) -> ClaudeCodeResult:
    """
    Run Claude Code CLI with the given prompt.

    Returns a ClaudeCodeResult containing:
    - response: The final assistant message text
    - trace: Full JSON trace for deterministic scoring
    - commands: Extracted command executions
    - success: Whether execution completed successfully
    """
    # Build the command
    cmd = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "--output-format", "json",
    ]

    if model:
        cmd.extend(["--model", model])

    # Add the prompt
    cmd.append(prompt)

    # Run Claude Code
    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            env={**os.environ, "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")},
        )

        if result.returncode != 0:
            return ClaudeCodeResult(
                response=f"Error running Claude Code: {result.stderr}",
                trace=None,
                commands=[],
                success=False,
            )

        # Parse JSON output
        try:
            trace = json.loads(result.stdout)
        except json.JSONDecodeError:
            return ClaudeCodeResult(
                response=result.stdout,
                trace=None,
                commands=[],
                success=True,
            )

        # Extract the final assistant response
        response = ""
        if isinstance(trace, dict) and "result" in trace:
            response = trace["result"]
        elif isinstance(trace, list):
            # Find the last assistant message
            for msg in reversed(trace):
                if msg.get("type") == "assistant":
                    content = msg.get("content", [])
                    text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                    response = "\n".join(text_parts)
                    break

        # Extract commands for analysis
        commands = extract_commands_from_output(trace)

        return ClaudeCodeResult(
            response=response or result.stdout,
            trace=trace,
            commands=commands,
            success=True,
        )

    except subprocess.TimeoutExpired:
        return ClaudeCodeResult(
            response=f"Error: Claude Code timed out after {CLAUDE_TIMEOUT} seconds",
            trace=None,
            commands=[],
            success=False,
        )
    except Exception as e:
        return ClaudeCodeResult(
            response=f"Error running Claude Code: {str(e)}",
            trace=None,
            commands=[],
            success=False,
        )


@solver
def claude_code_solver(
    model: str | None = None,
    explicit_skill: bool = False,
) -> Solver:
    """
    Solver that runs Claude Code CLI with the dns-troubleshooter skill.

    This executes the actual Claude Code CLI rather than directly invoking the model,
    testing the skill as it would be used in practice.

    Args:
        model: Optional model override
        explicit_skill: If True, prompt explicitly mentions the skill name
    """

    async def solve(state: TaskState, generate) -> TaskState:
        # Create a temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)

            # Set up the skill in the working directory
            setup_skill_directory(work_dir)

            # Get the user's input prompt
            user_input = state.input_text

            # Build prompt with test DNS server context
            # Support both doggo (preferred) and dig (fallback)
            if explicit_skill:
                skill_prefix = "Use your dns-troubleshooter skill to: "
            else:
                skill_prefix = ""

            full_prompt = f"""{skill_prefix}{user_input}

IMPORTANT: For all DNS queries, use the test DNS server at 127.0.0.1 port {DNS_PORT}.
- With doggo (preferred): doggo <record_type> <domain> @127.0.0.1:{DNS_PORT}
- With dig (fallback): dig @127.0.0.1 -p {DNS_PORT} <domain> <record_type>

When analyzing DNS records, provide:
1. Your finding
2. The command you used to verify
3. Your diagnosis (valid, invalid, warning, insecure, incomplete)
4. Explanation of the issue if any"""

            # Run Claude Code and get the response
            result = await asyncio.to_thread(
                run_claude_code, full_prompt, work_dir, model
            )

            # Store the execution trace in metadata for process goal scoring
            state.metadata["execution_trace"] = result.trace
            state.metadata["commands_executed"] = result.commands
            state.metadata["execution_success"] = result.success

            # Also preserve sample metadata (zone, scenario_id, etc.)
            # These are set by the sample creation functions

            # Create the model output
            state.output = ModelOutput.from_content(
                model="claude-code",
                content=result.response,
            )

            # Add assistant message to the conversation
            state.messages.append(
                ChatMessageAssistant(content=result.response)
            )

        return state

    return solve


@solver
def claude_code_negative_solver(model: str | None = None) -> Solver:
    """
    Solver for negative control tests.

    Does NOT add DNS server instructions - tests if skill triggers inappropriately.
    """

    async def solve(state: TaskState, generate) -> TaskState:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            setup_skill_directory(work_dir)

            # Use the prompt as-is, no DNS server context
            user_input = state.input_text

            result = await asyncio.to_thread(
                run_claude_code, user_input, work_dir, model
            )

            state.metadata["execution_trace"] = result.trace
            state.metadata["commands_executed"] = result.commands
            state.metadata["execution_success"] = result.success

            state.output = ModelOutput.from_content(
                model="claude-code",
                content=result.response,
            )

            state.messages.append(
                ChatMessageAssistant(content=result.response)
            )

        return state

    return solve


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
                    "zone": domain,
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
                    "zone": domain,
                },
            )
        )

    return samples


def create_negative_samples() -> list[Sample]:
    """
    Create negative control samples - prompts that should NOT trigger the skill.

    These test that the skill isn't invoked inappropriately.
    """
    samples = []

    for scenario_id, scenario in NEGATIVE_SCENARIOS.items():
        samples.append(
            Sample(
                input=scenario["prompt"],
                target=scenario["expected_behavior"],
                metadata={
                    "scenario_id": scenario_id,
                    "category": "negative_control",
                    "should_trigger_skill": False,
                },
            )
        )

    return samples


def create_all_samples() -> list[Sample]:
    """Create all positive evaluation samples (excludes negative controls)."""
    samples = []
    samples.extend(create_spf_samples())
    samples.extend(create_conflict_samples())
    return samples


@task
def dns_troubleshooter_eval() -> Task:
    """
    Main evaluation task for dns-troubleshooter skill using Claude Code CLI.

    Measures:
    - Outcome: Correct diagnosis (model_graded_fact)
    - Process: DNS tool used, test server queried
    - Style: Output format
    - Efficiency: Command count
    """
    start_dns_server()

    samples = create_all_samples()
    dataset = MemoryDataset(samples=samples, name="dns-troubleshooter-eval")

    return Task(
        dataset=dataset,
        solver=[
            claude_code_solver(),
        ],
        scorer=[
            model_graded_fact(),  # Outcome: correct diagnosis
            dns_tool_used(),  # Process: used doggo or dig
            test_server_queried(port=DNS_PORT),  # Process: queried test server
            correct_domain_queried(),  # Process: queried right domain
            command_efficiency(),  # Efficiency: reasonable command count
        ],
    )


@task
def dns_spf_eval() -> Task:
    """SPF-focused evaluation task using Claude Code CLI."""
    start_dns_server()

    samples = create_spf_samples()
    dataset = MemoryDataset(samples=samples, name="dns-spf-eval")

    return Task(
        dataset=dataset,
        solver=[
            claude_code_solver(),
        ],
        scorer=[
            model_graded_fact(),
            dns_tool_used(),
            test_server_queried(port=DNS_PORT),
        ],
    )


@task
def dns_conflict_eval() -> Task:
    """Record conflict evaluation task using Claude Code CLI."""
    start_dns_server()

    samples = create_conflict_samples()
    dataset = MemoryDataset(samples=samples, name="dns-conflict-eval")

    return Task(
        dataset=dataset,
        solver=[
            claude_code_solver(),
        ],
        scorer=[
            model_graded_fact(),
            dns_tool_used(),
            test_server_queried(port=DNS_PORT),
        ],
    )


@task
def dns_doggo_preference_eval() -> Task:
    """
    Evaluation task specifically measuring doggo vs dig preference.

    Tests whether Claude uses doggo (preferred) over dig (fallback).
    """
    start_dns_server()

    samples = create_all_samples()
    dataset = MemoryDataset(samples=samples, name="dns-doggo-preference-eval")

    return Task(
        dataset=dataset,
        solver=[
            claude_code_solver(),
        ],
        scorer=[
            doggo_preferred(),  # Scores higher for doggo usage
            model_graded_fact(),
        ],
    )


@task
def dns_explicit_skill_eval() -> Task:
    """
    Evaluation with explicit skill invocation.

    Tests whether explicitly mentioning the skill improves results.
    """
    start_dns_server()

    samples = create_all_samples()
    dataset = MemoryDataset(samples=samples, name="dns-explicit-skill-eval")

    return Task(
        dataset=dataset,
        solver=[
            claude_code_solver(explicit_skill=True),
        ],
        scorer=[
            model_graded_fact(),
            dns_tool_used(),
            test_server_queried(port=DNS_PORT),
            output_format_check(),
        ],
    )


@task
def dns_negative_control_eval() -> Task:
    """
    Negative control evaluation - prompts that should NOT trigger the skill.

    Tests that the skill isn't invoked inappropriately for:
    - General DNS questions (not troubleshooting)
    - Unrelated tasks
    - Informational queries
    """
    # Note: DNS server not strictly needed but start for consistency
    start_dns_server()

    samples = create_negative_samples()
    dataset = MemoryDataset(samples=samples, name="dns-negative-control-eval")

    return Task(
        dataset=dataset,
        solver=[
            claude_code_negative_solver(),
        ],
        scorer=[
            skill_not_triggered(),  # Should NOT use DNS tools
        ],
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
