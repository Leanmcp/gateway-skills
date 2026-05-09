# tau2-bench Export File Format

## Overview

Export files are plain text transcripts of a complete tau2-bench task evaluation. They contain metadata, expected/actual tool call sequences, KB documentation references, and the full conversation transcript.

## Sections

### 1. Metadata Header

```
RUN:    eval-20260715-223301-NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16
TASK:   task_041  TRIAL: 0
REWARD: 0.000
```

- **RUN**: Unique identifier for this evaluation run (model + timestamp)
- **TASK**: Task ID and trial number
- **REWARD**: Final score (0.0-1.0, where 1.0 = success)

### 2. Task Explanation

```markdown
★ TASK EXPLANATION (full picture)  task_041  — 16 lines · 3461 chars · 404 words

## task_041 — Complex multi-card dispute with provisional credit limits

- **Customer goal:** [Description of what the agent must accomplish]
- **Scenario & behavior:** [Context and constraints]
- **CRITICAL TRAP:** [Important gotchas the agent might miss]
- **Expected action(s) (the answer):**
  - action 1 — [who performs it: **agent** or **user**]
  - action 2
  - ...
```

**Key fields:**
- **Expected actions**: The ground truth tool calls the agent MUST make to succeed
- **Who performs**: **agent** = system must call; **user** = customer/user-sim must call
- **Graded on**: What criterion the task is scored against (e.g., `DB` = database results)
- **Key source docs**: Which KB documents are critical to solving this task

### 3. Tools Loaded

```
🛠 TOOLS LOADED (15 tools)  — 2142 tok · 8621 chars  (in every assistant call · → to expand)

KB_search
call_discoverable_agent_tool
change_user_email
get_credit_card_accounts_by_user
get_credit_card_transactions_by_user
get_current_time
...
```

**Meaning**: These are the tools/functions available to the agent during this run.

**Important**: KB documents are referenced here. Example:
```
doc_credit_cards_credit_card_account_logistics_007
doc_credit_cards_credit_cards_(general)_015
doc_credit_cards_credit_card_replacements_005
```

These are the knowledge base docs the agent can search for using `KB_search`.

### 4. Tool-Call Summary

```
⇄ TOOL-CALL SUMMARY  task_041  — 10 made · 16 expected

OURS — model's tool calls:
  [asst] KB_search(query="dispute charges fraud multiple cards")
  [asst] get_user_information_by_name(customer_name="Claire Dubois")
  [asst] get_current_time()
  [asst] log_verification(...)
  [asst] get_credit_card_accounts_by_user(user_id="a6a7d745b2")
  [asst] get_credit_card_transactions_by_user(user_id="a6a7d745b2")
  ...

GROUND TRUTH — expected:
  [asst] log_verification(...)
  [asst] unlock_discoverable_agent_tool(agent_tool_name="get_user_dispute_history_7291")
  [asst] call_discoverable_agent_tool(agent_tool_name="get_user_dispute_history_7291", ...)
  ...
```

**Key concepts:**
- **OURS**: What the agent actually called (in order)
- **GROUND TRUTH**: What the agent should have called to succeed
- **made · expected**: Number of tool calls made vs. number needed

**Matching the counts**:
- If `10 made · 16 expected`, agent made 10 calls but needed 16 to succeed
- If `18 made · 16 expected`, agent over-called (duplication or unnecessary steps)

### 5. Conversation Transcript

```markdown
────────────────────────────────────────────────────────────────────────
USER-SIM #0  phase=eval task=task_053 trial=0  (0 tok, finish=api)

Hi, I need help with two things...

────────────────────────────────────────────────────────────────────────
SYSTEM PROMPT (ASSISTANT)  phase=eval task=task_053 trial=0  — 74 lines · 6065 chars

<Instructions for the agent>

────────────────────────────────────────────────────────────────────────
ASSISTANT #2  phase=eval task=task_053 trial=0  (208 tok, finish=stop)

[THINKING]
...thinking process...

First, I need to search the KB for relevant information...

→ KB_search {"query": "dispute charge credit card transaction not received merchandise"}

────────────────────────────────────────────────────────────────────────
⇐ TOOL RESULT [ok]  — 504 lines · 24177 chars

1. How can I request a CLI?
   ID: doc_credit_cards_credit_card_account_logistics_004
   Score: 1.0000
   Content: [KB content]

────────────────────────────────────────────────────────────────────────
USER-SIM #5  phase=eval task=task_053 trial=0  (0 tok, finish=api)

Sure—my full name is Daniel Park-Hernandez.

────────────────────────────────────────────────────────────────────────
ASSISTANT #6  phase=eval task=task_053 trial=0  (61 tok, finish=stop)

[Conversation continues...]
```

**Round numbering**:
- `USER-SIM #0` → First user message
- `ASSISTANT #2` → Second assistant message
- `USER-SIM #5` → Fifth user message (both assistant and user are counted)
- `⇐ TOOL RESULT` → System response to a tool call

**Reading a round**:
1. Find the round marker (e.g., `ASSISTANT #8`)
2. Look for `[THINKING]` block (agent's reasoning)
3. Look for `→ tool_name(...)` lines (tool calls the agent made)
4. Find corresponding `⇐ TOOL RESULT` section (tool's response)

### 6. End-of-Episode Summary

```
■ EPISODE DONE  reward=0.0  phase=eval task=task_053 trial=0
```

Marks the end of the evaluation.

---

## How to Read a Failure

### Example: Missing Tool Call

**GROUND TRUTH**:
```
[asst] unlock_discoverable_agent_tool(agent_tool_name="get_user_dispute_history_7291")
[asst] call_discoverable_agent_tool(agent_tool_name="get_user_dispute_history_7291", ...)
```

**OURS**:
```
(Agent never calls these tools)
```

**What it means**: The agent should have checked the dispute history before filing disputes, but didn't. This is a MISSING TOOL CALL failure.

**How to find root cause**: Look in the transcript for:
- Did the agent consider checking dispute history?
- Did the agent search the KB for relevant docs?
- Was there a logical gap (agent didn't realize dispute history affects eligibility)?

### Example: Wrong Arguments

**GROUND TRUTH**:
```
[asst] call_discoverable_agent_tool(
  agent_tool_name="file_credit_card_transaction_dispute_4829",
  arguments="{\"eligible_for_provisional_credit\": true}"
)
```

**OURS**:
```
[asst] call_discoverable_agent_tool(
  agent_tool_name="file_credit_card_transaction_dispute_4829",
  arguments="{\"eligible_for_provisional_credit\": false}"
)
```

**What it means**: Agent called the right tool but with wrong parameter value. This is a ELIGIBILITY MISCALCULATION failure.

**How to find root cause**: 
- Did agent check account age (60+ days)?
- Did agent check dispute reason (fraud/duplicate/goods not received)?
- Did agent calculate transaction amount correctly?
- Did agent check previous disputes in past 12 months?

### Example: Wrong Sequencing

**GROUND TRUTH** (correct order):
```
1. [asst] submit_credit_limit_increase_request_7392(...)
2. [asst] approve_credit_limit_increase_5847(...)
3. [asst] file_credit_card_transaction_dispute_4829(...)
```

**OURS** (wrong order):
```
1. [asst] file_credit_card_transaction_dispute_4829(...)
2. [asst] submit_credit_limit_increase_request_7392(...)  ← Too late! Dispute already filed
```

**What it means**: Agent called tools in wrong order. Policy says CLI can't be approved if dispute is pending. Agent should file CLI first, then dispute.

**Root cause analysis**: 
- Did agent read the policy?
- Did agent understand the conflict?
- Did agent recognize the sequencing requirement?

---

## Key Metrics

### Token Count
```
ASSISTANT #2  phase=eval task=task_053 trial=0  (208 tok, finish=stop)
```
- `208 tok` = tokens used in this turn
- `finish=stop` = reason response ended (stop token, max tokens, tool use, etc.)

### Success Indicators

- **Reward: 1.0** = Task succeeded completely
- **Reward: 0.5** = Partial success (some requirements met)
- **Reward: 0.0** = Task failed (missing critical actions or wrong results)

### Size Annotations
```
★ TASK EXPLANATION (full picture)  task_041  — 16 lines · 3461 chars · 404 words
```
- `16 lines` = number of lines in this section
- `3461 chars` = character count
- `404 words` = word count

---

## Common Patterns to Look For

### Pattern 1: Missing KB Search

**Problem**: Agent never searched KB for relevant docs.

**Evidence**: 
- No `KB_search(...)` calls in early rounds
- Agent proceeds without consulting docs
- Fails on a requirement that WAS in the KB

### Pattern 2: Eligibility Calculation Error

**Problem**: Agent marked dispute as eligible/ineligible incorrectly.

**Evidence**:
- `eligible_for_provisional_credit` flag differs from expected
- Agent didn't verify all eligibility criteria:
  - Account age ≥ 60 days
  - Dispute reason is eligible (fraud/duplicate/goods not received)
  - Transaction amount $25–$limit
  - ≤2 previous disputes in 12 months
  - Merchant contacted (for non-fraud)

### Pattern 3: Policy Conflict Not Recognized

**Problem**: Agent didn't recognize that two requests conflict.

**Evidence**:
- Two goals interact (e.g., CLI + dispute)
- Policy says "CLI not approved if dispute pending"
- Agent should sequence them in specific order
- Agent failed to recognize the dependency

### Pattern 4: User Failure

**Problem**: User-sim made wrong arguments or didn't follow instructions.

**Evidence**:
- `[user]` tool call in OURS has wrong parameter
- User didn't provide required information when asked
- User called tool with incorrect account ID

---

## Questions to Ask When Analyzing

1. **Where did it fail?**
   - At what round number?
   - Which tool call was the first divergence?

2. **Why did it fail?**
   - Missing logic? (agent didn't think to call tool X)
   - Missing knowledge? (agent didn't search/find relevant KB doc)
   - Wrong reasoning? (agent understood policy but calculated wrong)
   - Ambiguous policy? (multiple interpretations possible)

3. **Was the information available?**
   - Check `🛠 TOOLS LOADED` for KB docs
   - Was the relevant doc loaded?
   - Did agent search for it?
   - If yes, did agent find it and understand it?

4. **What's the impact?**
   - Does this failure block other steps?
   - Does it make the entire task unsolvable?
   - Can the task be partially completed?

---

## Useful Abbreviations

| Abbreviation | Meaning |
|---|---|
| KB | Knowledge Base |
| KB_search | Search the KB for documents matching a query |
| asst | Assistant (the AI model) |
| user | User-Sim (simulated customer) |
| CLI | Credit Limit Increase |
| txn_* | Transaction ID |
| cc_* | Credit Card Account ID |
| doc_* | Knowledge Base Document ID |
| DB | Database (grading: check actual database results) |
| tok | Tokens (measures model's computation) |

---

## See Also

- `analyze_failures.py` — Script to programmatically analyze failures
- `parse_export.py` — Script to parse export files
