# Common Failure Patterns in tau2-bench

This guide helps you quickly identify and understand common failure patterns in task exports.

## Pattern 1: Missing Dispute History Check

### Signature
```
⇄ TOOL-CALL SUMMARY
OURS — missing:
  [asst] unlock_discoverable_agent_tool(agent_tool_name="get_user_dispute_history_7291")
  [asst] call_discoverable_agent_tool(agent_tool_name="get_user_dispute_history_7291", ...)
```

### Why It Happens
Agent doesn't recognize that previous disputes affect **provisional credit eligibility caps**. Policy states: "Customer can receive provisional credit on max 2 disputes in 12 months."

### Root Cause Categories
- **Policy misunderstanding**: Agent didn't read the provisional credit guidelines
- **Missing KB search**: Agent didn't search for "dispute history" or "provisional credit"
- **Incomplete verification**: Agent verified identity but not prior dispute count

### How to Find in Transcript
1. Look for when agent starts filing disputes
2. Search backward for any mention of "dispute history"
3. Check if agent called `get_user_dispute_history_7291`
4. If not found, agent skipped this critical step

### Impact
- Disputes marked as `eligible_for_provisional_credit: true` when they should be `false`
- Agent exhausts the cap without realizing it
- Task fails if it requires correct eligibility calculations

### Fix
Agent must call `get_user_dispute_history_7291` **before** filing disputes to:
1. Count how many disputes were already filed in past 12 months
2. Check if any received provisional credit
3. Calculate remaining eligibility

---

## Pattern 2: CLI + Dispute Sequencing Error

### Signature
```
Expected order:
  1. submit_credit_limit_increase_request_7392
  2. approve_credit_limit_increase_5847
  3. file_credit_card_transaction_dispute_4829

Actual order:
  1. file_credit_card_transaction_dispute_4829  ← WRONG!
  2. submit_credit_limit_increase_request_7392
```

### Why It Happens
Agent doesn't recognize the **policy conflict**: "CLI approval requires no pending disputes."

### Root Cause
- **Policy misunderstanding**: Agent didn't read doc_credit_cards_credit_card_account_logistics_007
  - Step 2 (Verify Basic Eligibility) lists: "No Pending Disputes" as requirement
  - Filing a dispute creates a "pending dispute" state
  - Therefore, dispute must be filed **after** CLI approval, not before

### How to Find in Transcript
1. Search for when customer mentions both requests (CLI + dispute)
2. Check order of tool calls
3. Look for any mention of "conflict" or "which first"
4. If dispute filed before CLI approval, this is the failure

### Impact
- Dispute blocks CLI approval
- Neither goal is fully achieved
- Task reward = 0.0 if both are required

### Fix
Agent must:
1. Recognize the conflict (read Step 2 of doc_credit_cards_credit_card_account_logistics_007)
2. Process CLI first: `submit_credit_limit_increase_request_7392` → `approve_credit_limit_increase_5847`
3. Only then file dispute: `file_credit_card_transaction_dispute_4829`

### Related Docs
- doc_credit_cards_credit_card_account_logistics_007 (step-by-step CLI workflow)
- doc_credit_cards_credit_card_account_logistics_005 (CLI eligibility requirements)

---

## Pattern 3: Provisional Credit Eligibility Miscalculation

### Signature
```
Expected:
  eligible_for_provisional_credit: true  (fraud charge, $500, account 200+ days old)

Actual:
  eligible_for_provisional_credit: false
```

### Why It Happens
Agent didn't verify **all five** eligibility criteria:

1. ✅ Account standing: Account open ≥ 60 days
2. ✅ Dispute reason: Must be `unauthorized_fraudulent_charge`, `duplicate_charge`, or `goods_services_not_received` (30+ days)
3. ✅ Dispute amount: $25 ≤ amount ≤ card's tier max
4. ✅ Previous disputes: ≤ 2 in past 12 months
5. ✅ Contacted merchant: For non-fraud disputes, customer must have tried resolving with merchant first

### Common Mistakes
- **Mistake 1**: Ignoring the 30-day rule for "goods not received"
  - Only eligible if purchase was > 30 days ago
  - If purchase was 20 days ago, NOT eligible
  
- **Mistake 2**: Missing the merchant contact requirement
  - Fraud disputes don't require contacting merchant
  - But duplicate/goods-not-received/etc. DO require it
  - If customer never contacted merchant, set `contacted_merchant: false` → ineligible

- **Mistake 3**: Not checking the provisional credit cap per card tier
  - Entry tier: max $2,500
  - Mid tier: max $5,000
  - Premium tier: max $10,000
  - If transaction is $6,000 on mid-tier card, NOT eligible

- **Mistake 4**: Forgetting the "not more than 2 disputes" rule
  - If customer already filed 3 disputes in past 12 months, this one is ineligible
  - Check `get_user_dispute_history_7291` result

### How to Find in Transcript
1. Find `file_credit_card_transaction_dispute_4829` calls
2. Look at `eligible_for_provisional_credit` parameter
3. Compare against GROUND TRUTH
4. If mismatch, search backward in transcript for:
   - Did agent check account age?
   - Did agent check dispute reason?
   - Did agent check merchant contact?
   - Did agent check transaction amount?
   - Did agent check dispute history?

### Impact
- Disputes get provisional credit when they shouldn't (leaves money on table, wastes program)
- Disputes denied provisional credit when eligible (customer unhappy, policy violation)
- Task fails if it requires correct eligibility calculations

### Fix
Agent must verify **all five criteria** before setting `eligible_for_provisional_credit`.

### Related Docs
- doc_credit_cards_credit_cards_(general)_015 (Provisional Credit Eligibility Guidelines)
- doc_credit_cards_credit_card_account_logistics_006 (Payment history requirements, tier limits)

---

## Pattern 4: User-Provided Wrong Arguments

### Signature
```
Expected:
  [user] call_discoverable_user_tool(discoverable_tool_name="get_card_last_4_digits", 
    arguments="{\"credit_card_account_id\": \"cc_a6a7d745b2_gold\"}")

Actual:
  [user] call_discoverable_user_tool(discoverable_tool_name="get_card_last_4_digits",
    arguments="{\"card_account_id\": \"cc_a6a7d745b2_gold\"}")  ← WRONG PARAM NAME
```

### Why It Happens
- User-sim (customer in simulation) provided wrong argument
- Typo or misunderstanding of parameter name
- Parameter should be `credit_card_account_id`, not `card_account_id`

### Root Cause
- **User action**, not agent action
- Agent provided the tool to the user with correct parameter name
- User didn't follow instructions or made a typo

### How to Find in Transcript
1. Look for `[user]` entries with tool calls
2. Check if parameter names match the tool definition
3. If parameter name is slightly off, this is user error

### Impact
- Depends on the context, but typically the tool call fails
- Agent must recover by re-explaining or providing the tool again
- May waste rounds/tokens

### Fix
Not an agent failure. User-sim should use exact parameter names as provided by agent.

---

## Pattern 5: KB Search Returned Results But Agent Didn't Use Them

### Signature
```
Transcript shows:
  → KB_search {"query": "dispute charge limit cap"}
  ⇐ TOOL RESULT [ok]
    doc_credit_cards_credit_cards_(general)_015
    [Contents about provisional credit caps]

But then:
  [Later] eligible_for_provisional_credit: true  ← Uses wrong cap!
```

### Why It Happens
- Agent searched KB
- KB returned relevant doc
- Agent didn't read/understand the result
- Or agent read it but miscalculated

### Root Cause Categories
- **Incomplete reading**: Agent saw the doc title but didn't read the body
- **Misunderstanding**: Agent misinterpreted what the doc said
- **Calculation error**: Agent read correctly but did math wrong
- **Context length issue**: KB result was long; agent lost focus or missed key section

### How to Find in Transcript
1. Search for `KB_search` calls
2. Find corresponding `⇐ TOOL RESULT` section
3. Read what the KB returned
4. Check if agent's later actions match the KB content
5. If not, agent understood KB incorrectly

### Impact
- Agent has the information but uses it wrong
- Task fails due to misinterpretation, not missing information

### Fix
Agent should:
1. Search KB for relevant topics
2. Read the full result (don't stop after title)
3. Extract key constraints/rules
4. Apply them explicitly to the current problem

---

## Pattern 6: Incomplete Verification

### Signature
```
Expected:
  [asst] log_verification(name="Claire Dubois", user_id="a6a7d745b2", 
    address="...", email="...", phone="...", date_of_birth="...")

Actual:
  [asst] log_verification(name="Claire Dubois", user_id="a6a7d745b2")
    ← Missing: address, email, phone, date_of_birth
```

### Why It Happens
Agent verified some identity fields but not all. Policy requires:
- Verify 2 out of 4: DOB, email, phone, address
- Then log all verified information

### Root Cause
- Agent only verified 2 fields (which is enough to proceed)
- But didn't gather/log the complete address/other info
- Left incomplete verification record

### Impact
- Audit trail is incomplete
- Customer service record is missing data
- Task fails if it requires full verification logging

### Fix
When verifying, gather and log **all available customer info**, not just the minimum.

---

## Quick Diagnostic Checklist

When analyzing a failing export, ask these questions in order:

- [ ] **Was dispute history checked?** (`get_user_dispute_history_7291` called?)
- [ ] **Is sequencing correct?** (CLI before dispute? Verification before tool calls?)
- [ ] **Are eligibility criteria verified?** (All 5 for provisional credit? All 3 for CLI?)
- [ ] **Did agent search KB for relevant docs?** (Look for `KB_search` calls)
- [ ] **If KB was searched, did agent use the results?** (Compare results to agent's actions)
- [ ] **Are all required tool calls present?** (Compare OURS vs GROUND TRUTH counts)
- [ ] **Are arguments correct?** (Parameter names, types, values match expected?)
- [ ] **Is this a user error?** (Look for `[user]` tool calls with wrong args)

---

## References

- **Dispute/Provisional Credit**: doc_credit_cards_credit_cards_(general)_015
- **CLI Eligibility**: doc_credit_cards_credit_card_account_logistics_005, doc_credit_cards_credit_card_account_logistics_007
- **Payment History**: doc_credit_cards_credit_card_account_logistics_006
- **Dispute History**: doc_credit_cards_credit_cards_(general)_016
- **Card Last 4 Digits**: doc_credit_cards_credit_cards_(general)_013
