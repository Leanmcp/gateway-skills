---
name: analyze-exports
description: Analyze tau2-bench task export files to identify exactly where and why tasks failed. Map failures to specific conversation rounds, show root causes, check whether relevant documentation was available, and cite sources. Use this skill whenever you need to debug a tau2-bench evaluation, understand why an agent made wrong decisions, identify missing knowledge, or review task performance—especially when context length, eligibility criteria, or policy compliance might be at fault.
---

# Analyze Exports Skill

## Purpose

When a tau2-bench task returns reward 0.0 (or fails), the export file contains everything you need to understand why—but it's buried in tool-call summaries and conversation transcripts. This skill systematically analyzes the export to show:

1. **Where it failed** — the exact round (Assistant #X, User #Y) and tool-call sequence
2. **What should have happened** — ground truth from the task explanation
3. **Why it failed** — root cause (missing logic, wrong arguments, bad order, policy misunderstanding)
4. **Was the docs available?** — whether the KB had the answer the agent needed
5. **Evidence** — quotes and citations from both the transcript and source documents

## Input Format

An export file (plain text) containing:
- `RUN:` and `TASK:` metadata
- `★ TASK EXPLANATION` (success criteria, expected actions)
- `🛠 TOOLS LOADED` (available tools and KB docs)
- `⇄ TOOL-CALL SUMMARY` (OURS vs GROUND TRUTH comparison)
- Full conversation transcript with tool calls and results

## Output Format & File Organization

Analysis reports are saved in a standardized folder structure for easy organization and review:

```
FAILURE_ANALYSIS/
├── analysis/
│   ├── hard_15/
│   │   ├── task_037_detailed_analysis.md
│   │   ├── task_038_detailed_analysis.md
│   │   ├── task_039_detailed_analysis.md
│   │   └── task_041_detailed_analysis.md
│   ├── hard_16/
│   │   ├── task_053_detailed_analysis.md
│   │   └── task_054_detailed_analysis.md
│   └── [other_categories]/
│       └── [task_id]_detailed_analysis.md
└── README.md (overview of all analyses)
```

**File Naming Convention**: `[task_id]_detailed_analysis.md`

**Folder Organization**: Group by difficulty level (hard_15, hard_16, etc.) or category to match your existing structure.

**Each analysis file contains these sections:**

### Report Structure

You will receive a structured analysis report with these sections:

```
## Export Analysis: [TASK_ID]

### Overview
- **Status**: PASS / FAIL
- **Reward**: [0.0-1.0]
- **Model**: [Model ID]
- **Duration**: [Time]

### Executive Summary
[1-2 sentence summary of what went wrong and why]

### Failure Map
**Failure Point #1: [Description]**
- **Round**: [Assistant #X → User #Y → Assistant #Z]
- **Tool Call Sequence**: [Call 1] → [Call 2] → [Missing: Call 3]
- **Who Failed**: Agent / User / System
- **Expected Action**: [What should have happened per GROUND TRUTH]
- **Actual Action**: [What the agent/user actually did]

[Details, quotes from transcript, tool results]

**Root Cause**: [Why did this happen?]
- **Category**: Missing tool call / Wrong arguments / Wrong order / Policy misunderstanding / Eligibility miscalculation
- **Evidence**: [Quote from transcript showing the decision point]

**Was docs available?** 
- **Yes** — Doc: [doc_id] found in TOOLS LOADED section
- **Quote**: [Relevant passage from KB]
- **Why agent didn't use it**: [Analysis of gap between available info and agent's reasoning]
- **No** — Agent would have needed [doc_id] but it wasn't loaded

**Impact**: [What downstream actions were blocked?]

---

### All Failures (Summary Table)
| Failure | Round | Category | Root Cause | Docs Available? |
|---------|-------|----------|-----------|-----------------|
| ... | ... | ... | ... | Yes/No |

### Recommendations
1. [What the agent should have done]
2. [What docs or logic were missing]
3. [How to prevent this in future runs]

### Appendix: Transcript Excerpts
[Relevant quotes from the conversation at decision points]
```

## How to Use This Skill

**Step 1: Paste the export file** (text) into your message, then ask one of these questions:

- `"Analyze this export and show me why task_041 got 0.0"`
- `"Walk me through where this failed and check if the docs had the answers"`
- `"Which round did things go wrong? Show me the exact tool calls."`
- `"Why did the agent mark disputes as eligible when they shouldn't be?"`
- `"Was the KB documentation available for this failure?"`
- `"IF NOTHING IS PROIVIDED YOU SHOULD ANALYZE FULLY AS ABOVE WHAT I HAD MENTIONED AND THEN POST IT INTO THE MARKDOWN FILE"`

**Step 2: Specify output location** (optional). The skill will save analysis to:
```
FAILURE_ANALYSIS/analysis/[task_name]/[task_id]_detailed_analysis.md
```

For example:
- `FAILURE_ANALYSIS/analysis/hard_15/task_041_detailed_analysis.md`
- `FAILURE_ANALYSIS/analysis/hard_15/task_053_detailed_analysis.md`

If you want a different location, specify it in your request:
- `"Analyze this export and save to FAILURE_ANALYSIS/analysis/hard_16/task_055_analysis.md"`

**The skill will:**
1. Parse the export structure
2. Compare OURS (actual) vs GROUND TRUTH (expected)
3. Identify divergence points
4. Map each failure to a specific round
5. Determine root cause
6. Check whether relevant docs were loaded
7. Cite sources for all findings
8. Show transcript excerpts at decision points
9. **Save detailed analysis to the specified output folder**

## Key Definitions

**Round**: A single back-and-forth in the conversation. Identified by `ASSISTANT #X`, `USER-SIM #Y`, or `⇐ TOOL RESULT`.

**Failure Category**:
- **Missing tool call**: Agent didn't call a required tool (should have unlocked/called but didn't)
- **Wrong arguments**: Agent called the right tool with bad parameters
- **Wrong order**: Agent called tools in incorrect sequence (e.g., filed dispute before checking history)
- **Policy misunderstanding**: Agent didn't follow eligibility rules or constraints
- **Eligibility miscalculation**: Agent marked something as eligible when it should be ineligible (or vice versa)

**Root Cause**: Why the agent made that specific mistake. Examples:
- Didn't search KB for relevant policy
- Searched KB but misunderstood the result
- Tool result was confusing or incomplete
- Agent forgot prior information
- Agent miscalculated (e.g., `provisional_credit_eligible` flag)
- Prompt/policy was ambiguous

**Docs Available?**
- **Yes**: The doc was in TOOLS LOADED section AND in the transcript (agent searched KB or had access)
- **Partially**: Doc was loaded but agent didn't search for it or search returned partial results
- **No**: Doc wasn't in TOOLS LOADED; agent couldn't have known.
## Example Analysis

**Input Export**:
```
TASK: task_053 TRIAL: 0
REWARD: 0.000
★ TASK EXPLANATION
Expected actions:
  - log_verification(...)
  - get_user_dispute_history_7291(...)
  - submit_credit_limit_increase_request_7392(...)
  - approve_credit_limit_increase_5847(...)
  - file_credit_card_transaction_dispute_4829(...)
```

**Skill Output (excerpt)**:
```
## Export Analysis: task_053

### Overview
- Status: FAIL
- Reward: 0.0
- Reason: CLI approval never submitted; dispute filed before CLI, violating policy conflict resolution

### Failure #1: Missing CLI Submission
- Round: After Assistant #8 (verification complete)
- Expected: unlock and call submit_credit_limit_increase_request_7392
- Actual: Agent never called this tool
- Root Cause: Agent didn't recognize that CLI must be processed BEFORE dispute (policy conflict)

**Was docs available?**
- **Yes** — doc_credit_cards_credit_card_account_logistics_007 was in TOOLS LOADED
- **Quote**: "Step 1: Submit the CLI Request... Step 2: Verify Basic Eligibility. ... No Pending Disputes"
- **Why agent didn't use it**: Agent retrieved dispute history but didn't correlate it to the CLI eligibility rule (Step 2, requirement 3). The policy conflict (CLI blocks if dispute pending, dispute creates pending state) required inference across docs.

**Impact**: 
- CLI request was never submitted
- Dispute was filed (or blocked on CLI)
- Customer goal of "both CLI approved and dispute filed" not met
- Reward: 0.0
```

## Important Notes

1. **This skill reads exports as-is** — it doesn't run the task again. It analyzes the transcript that already happened.

2. **Root cause analysis requires inference** — sometimes the "why" isn't obvious from tool calls alone. The skill reads between the lines: missed KB searches, forgotten prior context, logical errors.

3. **Policy conflicts are key** — tau2-bench tasks often test whether agents recognize when two requests interact (e.g., CLI + dispute). The skill flags these.

4. **Provisional credit and eligibility calculations** — disputes exports often involve calculating whether disputes qualify for provisional credit. The skill checks:
   - Did agent check dispute history?
   - Did agent apply the cap correctly?
   - Were eligibility criteria (account age, purchase date, merchant contact, reason code) verified?

5. **Multi-step failures** — one missed tool call can cascade. The skill traces dependencies: if the agent didn't call get_dispute_history early, all downstream eligibility flags are suspect.

## Troubleshooting

**"The export is incomplete"**  
Some exports may be truncated. The skill will note what information is missing and work with what's available.

**"I don't understand the root cause"**  
Ask the skill to elaborate: *"Explain the root cause in simpler terms"* or *"What KB search should the agent have done?"*

**"The skill says docs were available but I don't see them in my export"**  
Check the `🛠 TOOLS LOADED` section. Docs are listed as `doc_credit_cards_credit_card_account_logistics_007`, etc. If it's not there, the docs weren't loaded for that run.

---

## Script Dependencies

The skill uses bundled Python scripts to:
- Parse export structure (YAML sections, conversation rounds)
- Map tool calls to conversation rounds
- Extract KB doc references from TOOLS LOADED
- Compare OURS vs GROUND TRUTH tool calls
- Generate the structured report

See `scripts/` directory for implementation.
