#!/usr/bin/env python3
"""
Generate structured failure analysis from parsed export data.

Analyzes:
- Where tool calls diverge from expected
- Which round each failure occurred in
- Root causes (missing tool, wrong args, wrong order, policy misunderstanding)
- Whether relevant KB docs were available
- Impact of each failure
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class FailureCategory(Enum):
    MISSING_TOOL_CALL = "Missing tool call"
    WRONG_ARGUMENTS = "Wrong arguments"
    WRONG_ORDER = "Wrong order/sequencing"
    POLICY_MISUNDERSTANDING = "Policy misunderstanding"
    ELIGIBILITY_MISCALCULATION = "Eligibility miscalculation"
    KB_SEARCH_FAILURE = "KB search failure"
    INCOMPLETE_VERIFICATION = "Incomplete verification"


@dataclass
class Failure:
    failure_id: int
    description: str
    round_number: int
    category: FailureCategory
    expected: str
    actual: str
    root_cause: str
    docs_available: Optional[str]  # doc ID if available
    doc_quote: Optional[str]
    why_not_used: str
    impact: str
    transcript_excerpt: str


def analyze_tool_call_divergence(actual: List[str], expected: List[str]) -> List[Failure]:
    """
    Compare actual vs expected tool calls and identify divergence points.

    Returns failures ranked by impact.
    """
    failures = []
    failure_id = 1

    # Find first divergence
    for i in range(max(len(actual), len(expected))):
        if i >= len(actual):
            # Expected more tool calls but actual stopped
            exp = expected[i]
            failures.append(Failure(
                failure_id=failure_id,
                description=f"Missing tool call at position {i+1}",
                round_number=i,  # Approximation
                category=FailureCategory.MISSING_TOOL_CALL,
                expected=exp,
                actual="(no action taken)",
                root_cause="Agent did not recognize the need for this tool call or didn't have the information to proceed",
                docs_available=None,
                doc_quote=None,
                why_not_used="Unknown - requires transcript analysis",
                impact=f"Blocked subsequent actions; unable to complete step {i+1} of workflow",
                transcript_excerpt=""
            ))
            failure_id += 1

        elif i >= len(expected):
            # Actual had more tool calls than expected - might be duplication
            act = actual[i]
            failures.append(Failure(
                failure_id=failure_id,
                description=f"Unexpected tool call at position {i+1}",
                round_number=i,
                category=FailureCategory.WRONG_ORDER,
                expected="(no action)",
                actual=act,
                root_cause="Agent made unnecessary or out-of-order tool calls",
                docs_available=None,
                doc_quote=None,
                why_not_used="Agent did not follow the required workflow sequence",
                impact="Wasted tokens; may have caused state misalignment",
                transcript_excerpt=""
            ))
            failure_id += 1

        elif actual[i].strip() != expected[i].strip():
            # Tool calls differ - extract tool names for comparison
            exp_tool = extract_tool_name(expected[i])
            act_tool = extract_tool_name(actual[i])

            if exp_tool != act_tool:
                # Different tool altogether
                category = FailureCategory.MISSING_TOOL_CALL if act_tool == "(none)" else FailureCategory.WRONG_ARGUMENTS
            else:
                # Same tool, different arguments
                category = FailureCategory.WRONG_ARGUMENTS

            failures.append(Failure(
                failure_id=failure_id,
                description=f"Tool call mismatch at position {i+1}",
                round_number=i,
                category=category,
                expected=expected[i],
                actual=actual[i],
                root_cause="Requires transcript analysis to determine exact reason",
                docs_available=None,
                doc_quote=None,
                why_not_used="Requires transcript analysis",
                impact=f"Step {i+1} produced incorrect results or was skipped",
                transcript_excerpt=""
            ))
            failure_id += 1

    return failures


def extract_tool_name(tool_call_str: str) -> str:
    """Extract tool name from a tool call string like '[asst] KB_search(...)'."""
    import re
    match = re.search(r'(\w+)\s*\(', tool_call_str)
    return match.group(1) if match else "(unknown)"


def categorize_failure(actual: str, expected: str, transcript_context: str) -> FailureCategory:
    """
    Infer failure category from actual vs expected and transcript.
    """
    if not actual or actual == "(none)":
        return FailureCategory.MISSING_TOOL_CALL

    exp_tool = extract_tool_name(expected)
    act_tool = extract_tool_name(actual)

    if exp_tool != act_tool:
        # Check for sequencing issues (e.g., filing dispute before checking history)
        if "dispute" in expected.lower() and "history" not in actual.lower():
            return FailureCategory.WRONG_ORDER

        return FailureCategory.MISSING_TOOL_CALL

    # Same tool, different args
    if "eligible_for_provisional_credit" in actual.lower():
        return FailureCategory.ELIGIBILITY_MISCALCULATION

    if "contact" in actual.lower() or "merchant" in actual.lower():
        return FailureCategory.POLICY_MISUNDERSTANDING

    return FailureCategory.WRONG_ARGUMENTS


def build_analysis_report(export_data, failures: List[Failure]) -> str:
    """Generate the full markdown analysis report."""
    report = []

    report.append(f"## Export Analysis: {export_data.task_id}")
    report.append("")
    report.append("### Overview")
    report.append(f"- **Status**: {'PASS' if export_data.reward > 0 else 'FAIL'}")
    report.append(f"- **Reward**: {export_data.reward}")
    report.append(f"- **Model**: {export_data.model}")
    report.append(f"- **Trial**: {export_data.trial}")
    report.append("")

    if not failures:
        report.append("### Executive Summary")
        report.append("No failures detected. Task completed successfully or exceeded expectations.")
    else:
        report.append("### Executive Summary")
        primary_failure = failures[0]
        report.append(f"Task failed at **{primary_failure.description.lower()}** (step {primary_failure.failure_id}).")
        report.append(f"Root cause: {primary_failure.root_cause}")
        report.append("")

        report.append("### Failure Details")
        report.append("")

        for failure in failures:
            report.append(f"**Failure #{failure.failure_id}: {failure.description}**")
            report.append("")
            report.append(f"- **Round**: {failure.round_number}")
            report.append(f"- **Category**: {failure.category.value}")
            report.append(f"- **Expected**: `{failure.expected}`")
            report.append(f"- **Actual**: `{failure.actual}`")
            report.append("")
            report.append(f"**Root Cause**: {failure.root_cause}")
            report.append("")

            if failure.docs_available:
                report.append(f"**Was documentation available?** ✅ Yes")
                report.append(f"- **Document**: `{failure.docs_available}`")
                if failure.doc_quote:
                    report.append(f"- **Relevant Quote**: \"{failure.doc_quote}\"")
                report.append(f"- **Why not used**: {failure.why_not_used}")
            else:
                report.append(f"**Was documentation available?** ❌ No")
                report.append(f"- **Why not used**: {failure.why_not_used}")

            report.append("")
            report.append(f"**Impact**: {failure.impact}")
            report.append("")

        report.append("### Summary Table")
        report.append("")
        report.append("| # | Description | Category | Round | Docs Available? |")
        report.append("|---|-------------|----------|-------|-----------------|")
        for failure in failures:
            docs_avail = "✅ Yes" if failure.docs_available else "❌ No"
            report.append(f"| {failure.failure_id} | {failure.description} | {failure.category.value} | {failure.round_number} | {docs_avail} |")
        report.append("")

        report.append("### Recommendations")
        report.append("")
        report.append("To prevent similar failures:")
        for i, failure in enumerate(failures, 1):
            if "Missing" in failure.description:
                report.append(f"{i}. Ensure the agent checks the KB for `{failure.docs_available or 'relevant documentation'}` before proceeding")
            elif "Mismatch" in failure.description:
                report.append(f"{i}. Verify tool arguments match the expected schema (compare actual vs expected)")
            elif "Order" in failure.category.value:
                report.append(f"{i}. Enforce correct tool call order in the system prompt")

    report.append("")
    report.append("### Loaded Documentation")
    report.append("")
    if export_data.loaded_docs:
        for doc in export_data.loaded_docs:
            report.append(f"- `{doc}`")
    else:
        report.append("(No KB documents were loaded for this task)")

    return "\n".join(report)


if __name__ == "__main__":
    # Test
    print("Failure analysis engine loaded. Use via Python import.")
