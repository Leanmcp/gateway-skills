#!/usr/bin/env python3
"""
obs_adapters.py — platform adapters that turn ANY provider's response into the
one shape obs.Run.sample() records.

The whole point of splitting this from obs.py: the recording format is fixed and
platform-independent, so the only thing a new platform needs is a ~15-line
normalizer that answers five questions about a response —

    text      the raw decoded output (what the model literally produced)
    content   the visible reply after parsing (None if it only called tools)
    thinking  the reasoning trace, if the provider exposes one
    tool_calls [{"name": str, "arguments": dict}, ...]
    finish    stop | length | tool_calls | content_filter | ...
    usage     {"prompt_tokens": int, "completion_tokens": int}

Everything downstream (transcripts.jsonl, the viewers, the aggregators, the
diffing) then works identically for OpenAI, Gemini, Anthropic, LiteLLM, Tinker,
vLLM, or a model you serve yourself. Adding a platform is writing one function,
not re-plumbing observability.

Ships normalizers for the common ones plus `Observed*` wrappers that log a turn
around each call:

    from obs import Run
    from obs_adapters import ObservedOpenAI, ObservedGemini, ObservedAnthropic, \
        ObservedLiteLLM, log_tinker_turn, log_tool_results

    run = Run("eval", config={...}, root="runs")
    client = ObservedOpenAI(OpenAI(), run, role="agent")
    resp = client.chat(model="gpt-5.4-nano", messages=msgs, tools=tools)
    # ^ the turn is already in transcripts.jsonl; `resp` is the untouched SDK object

No provider SDK is imported at module import time — only inside the wrapper that
needs it — so this file is safe to import in an environment that has just one of
them installed.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

__all__ = [
    "Turn", "norm_openai", "norm_litellm", "norm_anthropic", "norm_gemini",
    "norm_auto", "ObservedOpenAI", "ObservedLiteLLM", "ObservedAnthropic",
    "ObservedGemini", "ObservedCallable", "log_tinker_turn", "log_tool_results",
]


# --------------------------------------------------------------------------- #
# the normalized turn
# --------------------------------------------------------------------------- #
@dataclass
class Turn:
    """One model generation, provider-independent."""

    text: str = ""
    content: Optional[str] = None
    thinking: Optional[str] = None
    tool_calls: list[dict] = field(default_factory=list)
    finish: Optional[str] = None
    usage: Optional[dict] = None
    cost: Optional[float] = None
    prompt_tokens: list[int] = field(default_factory=list)
    completion_tokens: list[int] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def log(self, run, role: str = "agent", **extra: Any) -> "Turn":
        """Record this turn on an obs.Run and return self (so you can chain)."""
        run.sample(
            role,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            text=self.text,
            content=self.content,
            thinking=self.thinking,
            tool_calls=self.tool_calls,
            finish=self.finish,
            usage=self.usage,
            cost=self.cost,
            **{**self.extra, **extra},
        )
        return self


def _loads(x: Any) -> Any:
    """Tool arguments arrive as a JSON string from most providers and as a dict
    from a few. Store dicts, so later analysis can diff fields instead of
    strings — but never lose a payload that fails to parse."""
    if isinstance(x, str):
        try:
            return json.loads(x)
        except (json.JSONDecodeError, ValueError):
            return x
    return x


# --------------------------------------------------------------------------- #
# normalizers
# --------------------------------------------------------------------------- #
def norm_openai(resp: Any) -> Turn:
    """OpenAI chat.completions (and anything wire-compatible: Fireworks,
    Together, vLLM's OpenAI server, OpenRouter, Groq, ...)."""
    choice = resp.choices[0]
    msg = choice.message
    content = getattr(msg, "content", None) or None
    # Reasoning models expose the trace under one of these, depending on the
    # provider's flavour of the OpenAI schema.
    thinking = (getattr(msg, "reasoning_content", None)
                or getattr(msg, "reasoning", None) or None)
    tool_calls = [
        {"name": tc.function.name,
         "arguments": _loads(tc.function.arguments),
         "id": getattr(tc, "id", None)}
        for tc in (getattr(msg, "tool_calls", None) or [])
    ]
    u = getattr(resp, "usage", None)
    usage = None
    if u is not None:
        usage = {"prompt_tokens": getattr(u, "prompt_tokens", None),
                 "completion_tokens": getattr(u, "completion_tokens", None),
                 "total_tokens": getattr(u, "total_tokens", None)}
    return Turn(
        text=content or "",
        content=content,
        thinking=thinking,
        tool_calls=tool_calls,
        finish=getattr(choice, "finish_reason", None),
        usage=usage,
        cost=getattr(resp, "_hidden_params", {}).get("response_cost")
        if hasattr(resp, "_hidden_params") else None,
        extra={"model": getattr(resp, "model", None)},
    )


# LiteLLM returns an OpenAI-shaped ModelResponse for EVERY provider it fronts
# (Vertex/Anthropic, Vertex/Gemini, OpenRouter, Bedrock, ...). That is why one
# runner can drive Claude, Gemini and Kimi with identical logging.
norm_litellm = norm_openai


def norm_anthropic(resp: Any) -> Turn:
    """Anthropic Messages API. Content is a list of typed blocks, so text,
    thinking and tool calls are separated for you — no parsing heuristics."""
    text_parts, thinking_parts, tool_calls = [], [], []
    for block in getattr(resp, "content", None) or []:
        btype = getattr(block, "type", None)
        if btype == "text":
            text_parts.append(getattr(block, "text", "") or "")
        elif btype in ("thinking", "redacted_thinking"):
            thinking_parts.append(getattr(block, "thinking", "") or "")
        elif btype == "tool_use":
            tool_calls.append({"name": getattr(block, "name", None),
                               "arguments": getattr(block, "input", None),
                               "id": getattr(block, "id", None)})
    u = getattr(resp, "usage", None)
    usage = None
    if u is not None:
        usage = {"prompt_tokens": getattr(u, "input_tokens", None),
                 "completion_tokens": getattr(u, "output_tokens", None),
                 "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", None),
                 "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", None)}
    content = "\n".join(p for p in text_parts if p) or None
    return Turn(
        text=content or "",
        content=content,
        thinking="\n".join(p for p in thinking_parts if p) or None,
        tool_calls=tool_calls,
        finish=getattr(resp, "stop_reason", None),
        usage=usage,
        extra={"model": getattr(resp, "model", None)},
    )


def norm_gemini(resp: Any) -> Turn:
    """Google Gemini (google-genai SDK). Parts carry either text, a
    `thought=True` text part (the reasoning summary), or a function_call."""
    text_parts, thinking_parts, tool_calls = [], [], []
    cands = getattr(resp, "candidates", None) or []
    finish = None
    if cands:
        cand = cands[0]
        finish = getattr(cand, "finish_reason", None)
        finish = getattr(finish, "name", finish)
        parts = getattr(getattr(cand, "content", None), "parts", None) or []
        for part in parts:
            fc = getattr(part, "function_call", None)
            if fc is not None:
                tool_calls.append({"name": getattr(fc, "name", None),
                                   "arguments": dict(getattr(fc, "args", None) or {}),
                                   "id": getattr(fc, "id", None)})
                continue
            ptext = getattr(part, "text", None)
            if ptext:
                (thinking_parts if getattr(part, "thought", False)
                 else text_parts).append(ptext)
    um = getattr(resp, "usage_metadata", None)
    usage = None
    if um is not None:
        usage = {"prompt_tokens": getattr(um, "prompt_token_count", None),
                 "completion_tokens": getattr(um, "candidates_token_count", None),
                 "thoughts_token_count": getattr(um, "thoughts_token_count", None),
                 "total_tokens": getattr(um, "total_token_count", None)}
    content = "\n".join(text_parts) or None
    return Turn(
        text=content or "",
        content=content,
        thinking="\n".join(thinking_parts) or None,
        tool_calls=tool_calls,
        finish=str(finish) if finish is not None else None,
        usage=usage,
        extra={"model": getattr(resp, "model_version", None)},
    )


def norm_auto(resp: Any) -> Turn:
    """Best-effort sniffing for a response whose provider you would rather not
    hardcode. Prefer an explicit normalizer when you know the platform — this
    exists so a quick script is never blocked on writing one."""
    if hasattr(resp, "choices"):
        return norm_openai(resp)
    if hasattr(resp, "candidates"):
        return norm_gemini(resp)
    if hasattr(resp, "content") and isinstance(getattr(resp, "content"), list):
        return norm_anthropic(resp)
    if isinstance(resp, dict) and "choices" in resp:
        class _O:  # dict -> attribute view, so norm_openai works unchanged
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, _O(v) if isinstance(v, dict)
                            else [_O(i) if isinstance(i, dict) else i for i in v]
                            if isinstance(v, list) else v)
        return norm_openai(_O(resp))
    return Turn(text=str(resp), content=str(resp), finish="unknown")


# --------------------------------------------------------------------------- #
# observed clients: call the provider, log the turn, hand back the SDK object
# --------------------------------------------------------------------------- #
class ObservedCallable:
    """Wrap ANY function that returns a provider response.

    This is the escape hatch for a platform with no wrapper below (a bespoke
    inference server, a colleague's `generate()`, a LangChain chain you can
    reach the raw response through). Give it the callable and a normalizer and
    every call is logged:

        gen = ObservedCallable(my_generate, run, role="agent",
                               normalizer=norm_openai)
        resp = gen(prompt=..., tools=...)
    """

    def __init__(self, fn: Callable[..., Any], run, *, role: str = "agent",
                 normalizer: Callable[[Any], Turn] = norm_auto,
                 system_prompt_of: Optional[Callable[..., Optional[str]]] = None):
        self._fn = fn
        self._run = run
        self._role = role
        self._norm = normalizer
        self._sysprompt_of = system_prompt_of

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self._sysprompt_of is not None:
            sp = self._sysprompt_of(*args, **kwargs)
            if sp:
                self._run.system_prompt(self._role, sp)
        t0 = time.time()
        try:
            resp = self._fn(*args, **kwargs)
        except Exception as e:
            self._run.error(f"{self._role}.generate", e, latency_s=round(time.time() - t0, 3))
            raise
        turn = self._norm(resp)
        turn.log(self._run, self._role, latency_s=round(time.time() - t0, 3))
        return resp


class ObservedOpenAI(ObservedCallable):
    """OpenAI SDK client. `client.chat(...)` == `client.chat.completions.create(...)`
    plus logging. The system message is pulled out of `messages` and logged once
    per session, so the conversation view is not buried under it every turn."""

    def __init__(self, client, run, *, role: str = "agent",
                 normalizer: Callable[[Any], Turn] = norm_openai):
        super().__init__(client.chat.completions.create, run, role=role,
                         normalizer=normalizer,
                         system_prompt_of=_openai_system_prompt)
        self.raw = client

    def chat(self, **kwargs: Any) -> Any:
        return self(**kwargs)


class ObservedLiteLLM(ObservedCallable):
    """LiteLLM `completion()` — one wrapper covering every provider it fronts.

    This is usually the highest-leverage adapter: `vertex_ai/gemini-3-pro`,
    `vertex_ai/claude-fable-5`, `openrouter/moonshotai/kimi-k3`, `gpt-5.4-nano`
    and a self-hosted `openai/...` endpoint all log identically, so a
    cross-model comparison is a change of one string."""

    def __init__(self, run, *, role: str = "agent",
                 normalizer: Callable[[Any], Turn] = norm_litellm):
        import litellm

        super().__init__(litellm.completion, run, role=role,
                         normalizer=normalizer,
                         system_prompt_of=_openai_system_prompt)

    def completion(self, **kwargs: Any) -> Any:
        return self(**kwargs)


class ObservedAnthropic(ObservedCallable):
    """Anthropic SDK client: `client.create(...)` == `messages.create(...)`."""

    def __init__(self, client, run, *, role: str = "agent",
                 normalizer: Callable[[Any], Turn] = norm_anthropic):
        super().__init__(client.messages.create, run, role=role,
                         normalizer=normalizer,
                         system_prompt_of=lambda **kw: kw.get("system"))
        self.raw = client

    def create(self, **kwargs: Any) -> Any:
        return self(**kwargs)


class ObservedGemini(ObservedCallable):
    """google-genai client: `client.generate(...)` == `models.generate_content(...)`."""

    def __init__(self, client, run, *, role: str = "agent",
                 normalizer: Callable[[Any], Turn] = norm_gemini):
        super().__init__(client.models.generate_content, run, role=role,
                         normalizer=normalizer,
                         system_prompt_of=_gemini_system_prompt)
        self.raw = client

    def generate(self, **kwargs: Any) -> Any:
        return self(**kwargs)


def _openai_system_prompt(*_args: Any, **kwargs: Any) -> Optional[str]:
    msgs = kwargs.get("messages") or []
    parts = []
    for m in msgs:
        role = m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
        if role in ("system", "developer"):
            c = m.get("content") if isinstance(m, dict) else getattr(m, "content", None)
            parts.append(c if isinstance(c, str) else json.dumps(c, default=str))
    return "\n\n".join(parts) or None


def _gemini_system_prompt(*_args: Any, **kwargs: Any) -> Optional[str]:
    cfg = kwargs.get("config")
    si = kwargs.get("system_instruction") or getattr(cfg, "system_instruction", None) \
        if cfg is not None else kwargs.get("system_instruction")
    if si is None and isinstance(cfg, dict):
        si = cfg.get("system_instruction")
    if si is None:
        return None
    return si if isinstance(si, str) else json.dumps(si, default=str)


# --------------------------------------------------------------------------- #
# token-level platforms (Tinker, vLLM raw, HF generate)
# --------------------------------------------------------------------------- #
def log_tinker_turn(run, role: str, *, prompt_tokens, completion_tokens,
                    text: str, parse: Callable[[str], Turn], **extra: Any) -> Turn:
    """Log one turn from a token-level platform.

    These are the platforms worth the extra care: you hold the exact token ids
    on both sides, which is what makes a trace replayable and a training run
    auditable — the tokens the policy was updated on are the tokens in the file.
    Hosted APIs cannot give you this, so never drop it when you have it.

    `parse` turns the decoded completion into a Turn (splitting <think> blocks,
    extracting tool calls in whatever format the chat template uses). That
    parser is model-family-specific; keep it next to the renderer that built
    the prompt, not here.
    """
    turn = parse(text)
    turn.prompt_tokens = list(prompt_tokens or [])
    turn.completion_tokens = list(completion_tokens or [])
    if not turn.text:
        turn.text = text
    return turn.log(run, role, **extra)


# --------------------------------------------------------------------------- #
# tool results
# --------------------------------------------------------------------------- #
def log_tool_results(run, messages: Any, requestor: str = "agent") -> None:
    """Mirror executed tool results into the run, in conversation order.

    Accepts an OpenAI-style list of `{"role": "tool", ...}` messages, a single
    such dict, or an object with `.content` / `.tool_messages`. Call it right
    before sampling the next turn: the orchestrator runs tools BETWEEN
    generations, so results never pass through a sample() call, and a trace
    with calls but no results cannot explain what the agent did next.
    """
    if run is None or messages is None:
        return
    items = messages if isinstance(messages, (list, tuple)) else [messages]
    for m in items:
        if isinstance(m, dict):
            if m.get("role") != "tool":
                continue
            run.tool_result(requestor=requestor, name=m.get("name"),
                            tool_call_id=m.get("tool_call_id"),
                            error=bool(m.get("error")),
                            content=str(m.get("content") or ""))
        elif hasattr(m, "tool_messages"):          # a multi-tool container
            log_tool_results(run, list(m.tool_messages), requestor)
        elif hasattr(m, "content"):
            run.tool_result(requestor=requestor,
                            name=getattr(m, "name", None),
                            tool_call_id=getattr(m, "id", None),
                            error=bool(getattr(m, "error", False)),
                            content=str(getattr(m, "content", "") or ""))
