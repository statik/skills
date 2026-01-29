"""
Custom InspectAI scorers for dns-troubleshooter skill evaluation.

These scorers implement deterministic checks for process goals:
- Did Claude use the right tools (doggo, dig)?
- Did Claude query the test DNS server?
- Was the output properly formatted?
"""

import re
from inspect_ai.scorer import (
    Scorer,
    Score,
    Target,
    scorer,
    CORRECT,
    INCORRECT,
    PARTIAL,
)
from inspect_ai.solver import TaskState


def extract_commands_from_trace(trace: dict | list | None) -> list[dict]:
    """
    Extract command execution events from a Claude Code JSON trace.

    The trace format from `claude --output-format json` contains messages
    with tool_use content blocks for command executions.
    """
    commands = []

    if trace is None:
        return commands

    # Handle list format (array of messages)
    if isinstance(trace, list):
        for msg in trace:
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

    # Handle dict format with messages key
    elif isinstance(trace, dict):
        messages = trace.get("messages", [])
        if messages:
            return extract_commands_from_trace(messages)

    return commands


def check_tool_in_commands(commands: list[dict], tool_name: str) -> bool:
    """Check if a specific tool was invoked in the commands."""
    tool_lower = tool_name.lower()
    for cmd in commands:
        command_str = cmd.get("command", "").lower()
        # Check if tool appears at start of command or after pipe/semicolon
        if re.search(rf'(^|\||;|&&|\s){tool_lower}\s', command_str):
            return True
    return False


def check_server_queried(commands: list[dict], host: str, port: int) -> bool:
    """Check if commands queried a specific DNS server."""
    for cmd in commands:
        command_str = cmd.get("command", "")
        # Check for dig format: @host -p port or @host:port
        if f"@{host}" in command_str and (f"-p {port}" in command_str or f"-p{port}" in command_str):
            return True
        # Check for doggo format: @host:port
        if f"@{host}:{port}" in command_str:
            return True
    return False


def check_domain_queried(commands: list[dict], domain: str) -> bool:
    """Check if a specific domain was queried."""
    domain_lower = domain.lower()
    for cmd in commands:
        command_str = cmd.get("command", "").lower()
        if domain_lower in command_str:
            return True
    return False


@scorer(metrics=["accuracy"])
def dns_tool_used() -> Scorer:
    """
    Scorer that checks if a DNS lookup tool (doggo or dig) was used.

    Returns CORRECT if doggo or dig was used, INCORRECT otherwise.
    Records which tool was used in the explanation.
    """
    async def score(state: TaskState, target: Target) -> Score:
        # Get the trace from metadata (set by solver)
        trace = state.metadata.get("execution_trace")
        commands = extract_commands_from_trace(trace)

        used_doggo = check_tool_in_commands(commands, "doggo")
        used_dig = check_tool_in_commands(commands, "dig")

        if used_doggo:
            return Score(
                value=CORRECT,
                answer="doggo",
                explanation="Used doggo DNS client (preferred tool)",
            )
        elif used_dig:
            return Score(
                value=CORRECT,
                answer="dig",
                explanation="Used dig DNS client (fallback tool)",
            )
        else:
            # Check for other DNS tools
            used_nslookup = check_tool_in_commands(commands, "nslookup")
            used_host = check_tool_in_commands(commands, "host")

            if used_nslookup or used_host:
                return Score(
                    value=PARTIAL,
                    answer="other",
                    explanation=f"Used {'nslookup' if used_nslookup else 'host'} instead of doggo/dig",
                )

            return Score(
                value=INCORRECT,
                answer="none",
                explanation=f"No DNS lookup tool detected. Commands: {[c.get('command', '') for c in commands]}",
            )

    return score


@scorer(metrics=["accuracy"])
def doggo_preferred() -> Scorer:
    """
    Scorer that specifically checks if doggo was used (preferred tool).

    Returns CORRECT if doggo was used, PARTIAL if dig was used, INCORRECT otherwise.
    """
    async def score(state: TaskState, target: Target) -> Score:
        trace = state.metadata.get("execution_trace")
        commands = extract_commands_from_trace(trace)

        used_doggo = check_tool_in_commands(commands, "doggo")
        used_dig = check_tool_in_commands(commands, "dig")

        if used_doggo:
            return Score(
                value=CORRECT,
                answer="doggo",
                explanation="Correctly used doggo as preferred DNS tool",
            )
        elif used_dig:
            return Score(
                value=PARTIAL,
                answer="dig",
                explanation="Used dig instead of preferred doggo",
            )
        else:
            return Score(
                value=INCORRECT,
                answer="none",
                explanation="No DNS lookup tool used",
            )

    return score


@scorer(metrics=["accuracy"])
def test_server_queried(host: str = "127.0.0.1", port: int = 5053) -> Scorer:
    """
    Scorer that checks if the test DNS server was queried.

    Args:
        host: Expected DNS server host
        port: Expected DNS server port
    """
    async def score(state: TaskState, target: Target) -> Score:
        trace = state.metadata.get("execution_trace")
        commands = extract_commands_from_trace(trace)

        if check_server_queried(commands, host, port):
            return Score(
                value=CORRECT,
                answer="yes",
                explanation=f"Correctly queried test DNS server at {host}:{port}",
            )
        else:
            return Score(
                value=INCORRECT,
                answer="no",
                explanation=f"Did not query test DNS server at {host}:{port}. Commands: {[c.get('command', '') for c in commands]}",
            )

    return score


@scorer(metrics=["accuracy"])
def correct_domain_queried() -> Scorer:
    """
    Scorer that checks if the expected domain was queried.

    Uses the 'zone' from sample metadata to determine expected domain.
    """
    async def score(state: TaskState, target: Target) -> Score:
        trace = state.metadata.get("execution_trace")
        commands = extract_commands_from_trace(trace)

        # Get expected domain from sample metadata
        expected_domain = state.metadata.get("zone", "")
        if not expected_domain:
            # Try to extract from scenario
            scenario_id = state.metadata.get("scenario_id", "")
            if scenario_id:
                from test_zones import SCENARIOS
                scenario = SCENARIOS.get(scenario_id, {})
                expected_domain = scenario.get("zone", "")

        if not expected_domain:
            return Score(
                value=INCORRECT,
                answer="unknown",
                explanation="Could not determine expected domain from metadata",
            )

        if check_domain_queried(commands, expected_domain):
            return Score(
                value=CORRECT,
                answer=expected_domain,
                explanation=f"Correctly queried domain: {expected_domain}",
            )
        else:
            return Score(
                value=INCORRECT,
                answer="wrong_domain",
                explanation=f"Did not query expected domain {expected_domain}. Commands: {[c.get('command', '') for c in commands]}",
            )

    return score


@scorer(metrics=["mean", "min", "max"])
def command_efficiency(min_commands: int = 1, max_commands: int = 5) -> Scorer:
    """
    Scorer that measures command efficiency.

    Returns a score from 0-1 based on whether command count is in expected range.

    Args:
        min_commands: Minimum expected commands (below this is suspicious)
        max_commands: Maximum expected commands (above this is inefficient)
    """
    async def score(state: TaskState, target: Target) -> Score:
        trace = state.metadata.get("execution_trace")
        commands = extract_commands_from_trace(trace)

        count = len(commands)

        if min_commands <= count <= max_commands:
            return Score(
                value=1.0,
                answer=str(count),
                explanation=f"Efficient: {count} commands (expected {min_commands}-{max_commands})",
            )
        elif count < min_commands:
            return Score(
                value=0.5,
                answer=str(count),
                explanation=f"Too few commands: {count} (expected at least {min_commands})",
            )
        else:
            # Scale down based on how many extra commands
            excess = count - max_commands
            penalty = min(excess * 0.1, 0.5)  # Max 50% penalty
            return Score(
                value=1.0 - penalty,
                answer=str(count),
                explanation=f"Inefficient: {count} commands (expected max {max_commands})",
            )

    return score


@scorer(metrics=["accuracy"])
def output_format_check() -> Scorer:
    """
    Scorer that checks if the output follows the expected format.

    Looks for the skill's required format elements:
    - "🔍 DNS Troubleshooter Analysis" header
    - Finding, Command, Interpretation, Recommendation sections
    """
    async def score(state: TaskState, target: Target) -> Score:
        output = state.output.completion if state.output else ""

        checks = {
            "header": "🔍" in output or "DNS Troubleshooter" in output,
            "finding": any(word in output.lower() for word in ["finding", "found", "discovered"]),
            "command": any(word in output.lower() for word in ["command", "dig", "doggo", "query"]),
            "diagnosis": any(word in output.lower() for word in ["diagnosis", "interpretation", "analysis", "result"]),
        }

        passed = sum(checks.values())
        total = len(checks)

        if passed == total:
            return Score(
                value=CORRECT,
                answer="complete",
                explanation="Output follows expected format",
            )
        elif passed >= total / 2:
            missing = [k for k, v in checks.items() if not v]
            return Score(
                value=PARTIAL,
                answer="partial",
                explanation=f"Missing format elements: {missing}",
            )
        else:
            return Score(
                value=INCORRECT,
                answer="incomplete",
                explanation=f"Output missing most format elements. Checks: {checks}",
            )

    return score


@scorer(metrics=["accuracy"])
def skill_not_triggered() -> Scorer:
    """
    Scorer for negative control tests - checks that the skill was NOT used.

    Returns CORRECT if no DNS tools were used, INCORRECT if they were.
    """
    async def score(state: TaskState, target: Target) -> Score:
        trace = state.metadata.get("execution_trace")
        commands = extract_commands_from_trace(trace)

        dns_tools = ["doggo", "dig", "nslookup", "host"]
        used_dns_tool = any(check_tool_in_commands(commands, tool) for tool in dns_tools)

        if not used_dns_tool:
            return Score(
                value=CORRECT,
                answer="not_triggered",
                explanation="Correctly did not invoke DNS troubleshooting skill",
            )
        else:
            return Score(
                value=INCORRECT,
                answer="triggered",
                explanation=f"Incorrectly triggered DNS skill. Commands: {[c.get('command', '') for c in commands]}",
            )

    return score
