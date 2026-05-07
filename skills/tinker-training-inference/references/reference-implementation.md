# Working code to read

Two bodies of real code this skill was written from, both in the `tau2-bench`
repo (`path/to/tau2-bench`). When you want a pattern
at full scale, with the project-specific parts still attached, read these.

## `START_TINKER/` — the tutorials

Everything here **actually executes** against the hosted service (it consumes
credits; the examples are kept small).

| file | what it shows |
| --- | --- |
| `tinker_quickstart_tutorial.py` | the canonical loops. `sft_single_step`, `sft_training_loop` (with a before/after sample), `rl_single_step`, `rl_training_loop` (sample → reward → group-relative advantage → `importance_sampling`), plus `download_weights()` doing the three-step save/sign/extract, and a forget-and-retrain demo |
| `full_finetune_tutorial.py` | full fine-tuning rather than LoRA |
| `wrong_capitals_finetune_tutorial.py` | deliberately corrupted SFT — a good way to *prove* your training pipeline actually changes the model, since the wrong answer is unmistakable |
| `inference_tinker.py` | sampling a `tinker://` checkpoint through the SDK; the clearest statement of why the local download is not needed to keep using the model |
| `tinker_openai_compat_1.py` | the OpenAI-compatible endpoint, raw `/completions`, and why raw-completion checkpoints must not be prompted through a chat template |
| `tinker_openai_compat_2.py` | tool calling over that endpoint |
| `tinker_openai_compat_3.py` | structured output — and the beta limitation: the endpoint ignores `json_schema`, so `.parse()` fails and you validate client-side |
| `inference_fireworks.py` | serving the exported adapter on another platform |
| `download_full_model.py` | merging the LoRA into the base with `peft.merge_and_unload()` to get a standalone HuggingFace model |
| `CLI_REFERENCE.md` | `tinker checkpoint` in full, including the sampler-vs-training download trap |
| `README.md` | concepts, API cheatsheet, loss-function list |

Run them:

```bash
python START_TINKER/tinker_quickstart_tutorial.py            # everything
python START_TINKER/tinker_quickstart_tutorial.py sft        # just the SFT loop
python START_TINKER/tinker_quickstart_tutorial.py rft-step   # one RL step
```

## `TAU2_WITH_TINKER/` — Tinker driving a real agent benchmark

This is the production shape: a multi-turn tool-using agent, an environment, a
simulated user, graded episodes, and RL over all of it.

| file | what to learn from it |
| --- | --- |
| `tinker_backend.py` | **the bridge.** `TinkerLM.generate_assistant` replaces a LiteLLM `generate()`: render → sample → decode → parse, returning a normal `AssistantMessage`, while recording `TurnRecord(prompt_tokens, completion_tokens, logprobs)` for RL. Contains every guard in [agentic-rl.md](agentic-rl.md) — context overflow, truncation retry, empty-output retry, duplicate-tool-call retry, the multi-tool-call continuation |
| `train_tau2_tinker.py` | the RL loop: rollouts → shaped reward → group-relative advantage → `build_rl_datum` → `forward_backward` → `optim_step`, plus periodic `save_state` / `save_weights_for_sampler`, mid-training eval off a saved sampler, resume, and thread-parallel rollouts |
| `eval_tau2_tinker.py` | eval-only path, and the one-config-dict-printed-and-written pattern |
| `config.py` | **every knob in one place**, each with the incident that set its value. Worth reading end to end — the comments are a log of what went wrong and why the default is what it is |
| `tool_bridge.py` | `render_prompt`, `build_tool_schemas`, `parse_completion` across Hermes / Harmony / typed-block formats |
| `obs.py`, `view_trace_tui.py` | the observability layer (generalized into the **research-observability** skill) |
| `multi_evals/` | one shared protocol runner + a thin script per model, so arms stay comparable |
| `PRICING_AFTER_JULY_17.md` | the price table this skill's catalogue was built from |

## Comments worth reading in `config.py`

That file records decisions that cost real runs to learn:

- why the default base model changed (a model at a 0.9% solve rate cannot
  separate any two arms — a floor at zero has no resolution)
- why `MODEL_CONTEXT_WINDOW` must be asserted against the service, and the 16
  episodes that died the day it was not
- why the simulated user's temperature was split out and set to 0.0, with the
  measured cost of leaving it at 0.5
- why `max_tokens` is 4096 for both speakers on reasoning models
- why multiple tool calls per turn is a chat-format question, and why the fix is
  a forced continuation rather than removing a stop string
