#!/usr/bin/env python3
"""
Parse tau2-bench task export files and extract structured data for analysis.

Parses:
- TASK metadata (task ID, trial, reward)
- TASK EXPLANATION (expected actions, success criteria)
- TOOLS LOADED (available KB docs)
- TOOL-CALL SUMMARY (OURS vs GROUND TRUTH)
- Conversation transcript with rounds
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum


class ActorType(Enum):
    ASSISTANT = "Assistant"
    USER = "User"
    SYSTEM = "System"


@dataclass
class ToolCall:
    round_number: int
    actor: ActorType
    action: str
    tool_name: str
    arguments: Optional[Dict] = None
    result: Optional[str] = None
    timestamp: Optional[int] = None

    def __repr__(self):
        args_str = f" {self.arguments}" if self.arguments else ""
        return f"[{self.actor.value} #{self.round_number}] {self.action}({self.tool_name}){args_str}"


@dataclass
class ConversationRound:
    round_number: int
    actor: ActorType
    message: str
    tool_calls: List[ToolCall]
    tool_results: List[str]


@dataclass
class ExportData:
    task_id: str
    trial: int
    reward: float
    model: str
    expected_actions: List[str]
    actual_actions: List[str]
    available_docs: List[str]
    loaded_docs: List[str]
    rounds: List[ConversationRound]
    task_explanation: str

    def diverge_at_index(self) -> Optional[int]:
        """Find first index where OURS and GROUND TRUTH diverge."""
        for i, (actual, expected) in enumerate(zip(self.actual_actions, self.expected_actions)):
            if actual.strip() != expected.strip():
                return i
        if len(self.actual_actions) < len(self.expected_actions):
            return len(self.actual_actions)
        return None


def extract_section(text: str, start_marker: str, end_marker: Optional[str] = None) -> str:
    """Extract text between two markers."""
    match = re.search(re.escape(start_marker) + r'(.*?)' + (re.escape(end_marker) if end_marker else r'(?=\n[A-Z\-]{4,}|$)'), text, re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_task_metadata(text: str) -> Tuple[str, int, float, str]:
    """Parse RUN, TASK, REWARD lines."""
    run_match = re.search(r'RUN:\s+(\S+)', text)
    task_match = re.search(r'TASK:\s+(\S+)\s+TRIAL:\s+(\d+)', text)
    reward_match = re.search(r'REWARD:\s+([\d.]+)', text)
    model_match = re.search(r'eval-([\d]{8}-[\d]{6})-(.+?)(?:\s|$)', text)

    task_id = task_match.group(1) if task_match else "unknown"
    trial = int(task_match.group(2)) if task_match else 0
    reward = float(reward_match.group(1)) if reward_match else 0.0
    model = model_match.group(2) if model_match else "unknown"

    return task_id, trial, reward, model


def parse_tool_calls(text: str, section_name: str) -> List[str]:
    """Parse tool calls from OURS or GROUND TRUTH section."""
    lines = text.split('\n')
    calls = []
    for line in lines:
        # Match patterns like: [asst] tool_name(...) or [user] tool_name(...)
        match = re.search(r'\[(asst|user)\]\s+(\w+)\s*\((.+?)\)(?:\s+→|$)', line)
        if match:
            calls.append(line.strip())
    return calls


def parse_conversation_rounds(text: str) -> List[ConversationRound]:
    """Extract conversation rounds from transcript."""
    rounds = []
    round_pattern = r'(ASSISTANT|USER-SIM|SYSTEM|⇐)\s+#?(\d+).*?\((.+?)\)'

    sections = re.split(r'\n(?=(?:ASSISTANT|USER-SIM|SYSTEM|⇐))', text)

    for section in sections:
        lines = section.split('\n', 1)
        if not lines[0].strip():
            continue

        header = lines[0]
        body = lines[1] if len(lines) > 1 else ""

        # Parse header
        if 'ASSISTANT' in header:
            actor = ActorType.ASSISTANT
            match = re.search(r'#(\d+)', header)
            round_num = int(match.group(1)) if match else 0
        elif 'USER' in header:
            actor = ActorType.USER
            match = re.search(r'#(\d+)', header)
            round_num = int(match.group(1)) if match else 0
        elif '⇐ TOOL RESULT' in header:
            actor = ActorType.SYSTEM
            match = re.search(r'\[(.+?)\]', header)
            round_num = int(match.group(1)) if match else 0
        else:
            continue

        # Extract tool calls from body
        tool_calls = []
        tool_results = []

        for line in body.split('\n'):
            if '→' in line and '(' in line:
                tool_calls.append(line.strip())
            if line.startswith('⇐'):
                tool_results.append(line.strip())

        round_obj = ConversationRound(
            round_number=round_num,
            actor=actor,
            message=body[:200],  # First 200 chars
            tool_calls=[],
            tool_results=tool_results
        )
        rounds.append(round_obj)

    return rounds


def parse_export(export_text: str) -> ExportData:
    """Parse complete export file."""
    task_id, trial, reward, model = parse_task_metadata(export_text)

    # Extract sections
    task_explanation = extract_section(export_text, "★ TASK EXPLANATION", "────")
    tools_section = extract_section(export_text, "🛠 TOOLS LOADED", "────")
    tool_summary = extract_section(export_text, "⇄ TOOL-CALL SUMMARY", "────")
    transcript = extract_section(export_text, "USER-SIM #0", None)

    # Parse KB docs
    loaded_docs = re.findall(r'(doc_\w+)', tools_section)

    # Parse tool calls
    ours_section = extract_section(tool_summary, "OURS —", "GROUND TRUTH")
    ground_truth_section = extract_section(tool_summary, "GROUND TRUTH —", None)

    actual_actions = parse_tool_calls(ours_section, "OURS")
    expected_actions = parse_tool_calls(ground_truth_section, "GROUND TRUTH")

    # Parse rounds
    rounds = parse_conversation_rounds(transcript)

    return ExportData(
        task_id=task_id,
        trial=trial,
        reward=reward,
        model=model,
        expected_actions=expected_actions,
        actual_actions=actual_actions,
        available_docs=[],
        loaded_docs=list(set(loaded_docs)),
        rounds=rounds,
        task_explanation=task_explanation
    )


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = parse_export(f.read())
        print(f"Task: {data.task_id}")
        print(f"Reward: {data.reward}")
        print(f"Expected actions: {len(data.expected_actions)}")
        print(f"Actual actions: {len(data.actual_actions)}")
        print(f"Diverge at: {data.diverge_at_index()}")
        print(f"Loaded docs: {data.loaded_docs}")
