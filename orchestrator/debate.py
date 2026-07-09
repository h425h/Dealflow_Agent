from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import anthropic

import config
from orchestrator.prompts import DEBATE_PROMPTS

_BACKOFF = [5, 10, 20]

SUBMIT_DEBATE_VERDICT_TOOL = {
    "name": "submit_debate_verdict",
    "description": (
        "Submit your synthesized verdict after reading the full bull/bear debate "
        "transcript. Mandatory — you must always call this, even if the debate "
        "did not converge."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["advance", "kill", "needs-more-info"],
                "description": (
                    "Your final synthesized verdict. Never omit this, even on "
                    "non-convergence — use 'needs-more-info' for genuine "
                    "non-convergence."
                ),
            },
            "confidence": {
                "type": "number",
                "description": (
                    "Confidence 0.0-1.0. Low confidence (0.1-0.3) is expected "
                    "and correct on genuine non-convergence."
                ),
            },
            "converged": {
                "type": "boolean",
                "description": (
                    "true only if bull and bear substantively converged on the "
                    "core thesis question — not merely that they were "
                    "adversarial by construction."
                ),
            },
            "convergence_summary": {
                "type": "string",
                "description": (
                    "What the debate converged on (if converged), or why it "
                    "structurally converged on the stronger argument despite "
                    "adversarial framing, or why it genuinely did not converge."
                ),
            },
            "resolving_question": {
                "type": "string",
                "description": (
                    "If converged=false: the SPECIFIC question whose answer "
                    "would resolve the disagreement. If you cannot name one, "
                    "the disagreement was structural, not substantive — set "
                    "converged=true instead. If converged=true, use an empty "
                    "string."
                ),
            },
            "rationale": {
                "type": "string",
                "description": (
                    "Full synthesis: which argument was stronger and why, or "
                    "exactly what remains unresolved. This is the deliverable "
                    "— do not write a separate short summary elsewhere."
                ),
            },
        },
        "required": [
            "verdict", "confidence", "converged",
            "convergence_summary", "resolving_question", "rationale",
        ],
    },
}


@dataclass
class DebateTurn:
    role: str   # "bull_opening" | "bear_opening" | "bull_rebuttal" | "bear_rebuttal"
    text: str


@dataclass
class DebateResult:
    company: str
    transcript: list         # list[DebateTurn]
    verdict: str
    confidence: float
    converged: bool
    convergence_summary: str
    resolving_question: Optional[str]
    rationale: str
    run_id: str
    timestamp: str
    usage: dict

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "transcript": [{"role": t.role, "text": t.text} for t in self.transcript],
            "verdict": self.verdict,
            "confidence": self.confidence,
            "converged": self.converged,
            "convergence_summary": self.convergence_summary,
            "resolving_question": self.resolving_question,
            "rationale": self.rationale,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "usage": self.usage,
        }


def _empty_usage() -> dict:
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }


def _accumulate(usage: dict, response) -> None:
    u = response.usage
    usage["input_tokens"] += u.input_tokens
    usage["output_tokens"] += u.output_tokens
    usage["cache_creation_input_tokens"] += getattr(u, "cache_creation_input_tokens", 0) or 0
    usage["cache_read_input_tokens"] += getattr(u, "cache_read_input_tokens", 0) or 0


def _call_with_backoff(sdk_client, **kwargs):
    for attempt, wait in enumerate([0] + _BACKOFF):
        if wait:
            time.sleep(wait)
        try:
            return sdk_client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            if attempt == len(_BACKOFF):
                raise


def _run_role_turn(sdk_client, role: str, user_content: str) -> tuple:
    """Single-shot, stateless turn for the bull or bear agent. No tools."""
    system_block = [{
        "type": "text",
        "text": DEBATE_PROMPTS[role],
        "cache_control": {"type": "ephemeral"},
    }]
    response = _call_with_backoff(
        sdk_client,
        model=config.MODEL,
        max_tokens=1024,
        system=system_block,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "\n".join(block.text for block in response.content if hasattr(block, "text"))
    return text, response


def _run_synthesizer(sdk_client, user_content: str) -> tuple:
    """Reads the full transcript and must call submit_debate_verdict. Allows one
    nudge retry if the model responds without calling the tool; falls back to an
    explicit, visibly-flagged needs-more-info/0.0 record if that also fails."""
    system_block = [{
        "type": "text",
        "text": DEBATE_PROMPTS["synthesizer"],
        "cache_control": {"type": "ephemeral"},
    }]
    messages = [{"role": "user", "content": user_content}]
    usage = _empty_usage()

    for _ in range(2):
        response = _call_with_backoff(
            sdk_client,
            model=config.MODEL,
            max_tokens=2048,
            system=system_block,
            tools=[SUBMIT_DEBATE_VERDICT_TOOL],
            messages=messages,
        )
        _accumulate(usage, response)

        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == "submit_debate_verdict":
                return block.input, usage

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": "You must call submit_debate_verdict now with your synthesis.",
        })

    return {
        "verdict": "needs-more-info",
        "confidence": 0.0,
        "converged": False,
        "convergence_summary": (
            "SYSTEM FAILURE: synthesizer did not call submit_debate_verdict after "
            "a retry nudge. This is not a genuine thesis-level non-convergence — "
            "it is a synthesis failure and should be treated as a bug, not a signal."
        ),
        "resolving_question": "N/A — system failure, not a genuine thesis question.",
        "rationale": (
            "Synthesizer failed to return a structured verdict after retry. "
            "Defaulting to needs-more-info / 0.0 confidence."
        ),
    }, usage


def _format_transcript(transcript: list) -> str:
    return "\n\n".join(
        f"--- {t.role.upper().replace('_', ' ')} ---\n{t.text}" for t in transcript
    )


def _save_debate(result: DebateResult) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe = result.company.lower().replace(" ", "_").replace("/", "_")
    path = config.DATA_DIR / f"{safe}_phase3debate_{result.run_id}.json"
    path.write_text(json.dumps(result.to_dict(), indent=2, default=str))


def run_debate(company_name: str, phase3_rubric: str) -> DebateResult:
    """Run the bull/bear/synthesizer debate on top of an already-completed Phase 3
    rubric. 2 rounds max (bull opening -> bear opening -> bull rebuttal -> bear
    rebuttal), hard cap, then synthesis. No new tool calls / searches anywhere in
    the debate — it reasons only over the rubric it's given.
    """
    sdk_client = anthropic.Anthropic()
    run_id = str(uuid.uuid4())[:8]
    usage = _empty_usage()

    evidence_header = (
        f"Company: {company_name}\n\n"
        f"Phase 3 rubric (evidence base — Phases 1-3a findings):\n{phase3_rubric}\n"
    )

    # Round 1 — opening cases
    bull_opening, resp = _run_role_turn(
        sdk_client, "bull", evidence_header + "\nWrite your opening BULL case now."
    )
    _accumulate(usage, resp)

    bear_opening, resp = _run_role_turn(
        sdk_client, "bear",
        evidence_header
        + f"\nBull's opening case:\n{bull_opening}\n\n"
        + "Write your opening BEAR case now, engaging the bull's specific claims. "
          "Include the conjunction-fallacy check as instructed.",
    )
    _accumulate(usage, resp)

    # Round 2 — rebuttals
    bull_rebuttal, resp = _run_role_turn(
        sdk_client, "bull",
        evidence_header
        + f"\nYour opening case:\n{bull_opening}\n\nBear's opening case:\n{bear_opening}\n\n"
        + "Write your REBUTTAL now. Engage the bear's specific claims directly — "
          "do not restate your opening case.",
    )
    _accumulate(usage, resp)

    bear_rebuttal, resp = _run_role_turn(
        sdk_client, "bear",
        evidence_header
        + f"\nYour opening case:\n{bear_opening}\n\nBull's rebuttal:\n{bull_rebuttal}\n\n"
        + "Write your REBUTTAL now. Engage the bull's rebuttal specifically — "
          "do not restate your opening case.",
    )
    _accumulate(usage, resp)

    transcript = [
        DebateTurn("bull_opening", bull_opening),
        DebateTurn("bear_opening", bear_opening),
        DebateTurn("bull_rebuttal", bull_rebuttal),
        DebateTurn("bear_rebuttal", bear_rebuttal),
    ]

    # Synthesis
    synth_prompt = (
        evidence_header
        + f"\nFull debate transcript:\n\n{_format_transcript(transcript)}\n\n"
        + "Render your synthesis now."
    )
    verdict_input, synth_usage = _run_synthesizer(sdk_client, synth_prompt)
    for k in usage:
        usage[k] += synth_usage[k]

    resolving_question = verdict_input.get("resolving_question") or None

    result = DebateResult(
        company=company_name,
        transcript=transcript,
        verdict=verdict_input["verdict"],
        confidence=float(verdict_input["confidence"]),
        converged=bool(verdict_input["converged"]),
        convergence_summary=verdict_input["convergence_summary"],
        resolving_question=resolving_question,
        rationale=verdict_input["rationale"],
        run_id=run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        usage=usage,
    )
    _save_debate(result)
    return result
