from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import anthropic

import config
from orchestrator.phases import PHASE_DEFINITIONS
from orchestrator.prompts import PHASE_PROMPTS


@dataclass
class PhaseVerdict:
    company: str
    phase: int
    verdict: str        # "advance" | "kill" | "needs-more-info"
    rationale: str
    confidence: float
    tool_calls: list
    run_id: str
    timestamp: str
    usage: dict         # accumulated token counts across all API calls in the phase


def _connector_tools(phase_number: int) -> list:
    """Build Anthropic tool definitions for a phase's connectors, plus the verdict tool."""
    phase = PHASE_DEFINITIONS[phase_number]
    tools = []
    _tool_descriptions = {
        "arxiv": "Search arXiv for academic papers, technical methods, and founder publications about a company or domain.",
        "tavily": "Search the web for business-model signal: company website, pricing page, press coverage, job postings.",
        "github": "Search GitHub for public repos, contributor counts, and commit activity. Absence of results is neutral, not negative.",
    }
    for c in phase.connectors:
        tools.append({
            "name": f"{c.name}_search",
            "description": _tool_descriptions.get(
                c.name,
                f"Search {c.name} for information about a company or topic.",
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                    "max_results": {
                        "type": "integer",
                        "description": (
                            f"Results to return (default {config.MAX_RESULTS_PER_CONNECTOR})."
                        ),
                    },
                },
                "required": ["query"],
            },
        })
    tools.append({
        "name": "submit_verdict",
        "description": (
            "Submit your final verdict for this phase. Call this once you have gathered "
            "enough information. This ends the phase and records the decision."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["advance", "kill", "needs-more-info"],
                    "description": (
                        "advance = proceed to next phase; "
                        "kill = stop diligence; "
                        "needs-more-info = flag for human review."
                    ),
                },
                "rationale": {
                    "type": "string",
                    "description": (
                        "2-4 sentences justifying the verdict. State what you found and "
                        "— critically — what the system could not determine."
                    ),
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence in this verdict (0.0–1.0).",
                },
            },
            "required": ["verdict", "rationale", "confidence"],
        },
    })
    return tools


def _call_connector(phase_number: int, tool_name: str, tool_input: dict) -> str:
    """Dispatch a connector tool call and return the result as a JSON string."""
    phase = PHASE_DEFINITIONS[phase_number]
    connector_name = tool_name[: -len("_search")]   # strip trailing "_search"
    connector = next((c for c in phase.connectors if c.name == connector_name), None)
    if connector is None:
        return json.dumps({"error": f"no connector named {connector_name!r}"})
    result = connector.search(
        query=tool_input["query"],
        max_results=tool_input.get("max_results", config.MAX_RESULTS_PER_CONNECTOR),
    )
    return json.dumps(result.to_dict())


def _serialize_messages(messages: list) -> list:
    """Convert Anthropic SDK content objects to plain dicts for JSON persistence."""
    out = []
    for m in messages:
        content = m["content"]
        if isinstance(content, str):
            out.append({"role": m["role"], "content": content})
        elif isinstance(content, list):
            blocks = []
            for block in content:
                if isinstance(block, dict):
                    blocks.append(block)
                elif hasattr(block, "model_dump"):
                    blocks.append(block.model_dump())
                else:
                    blocks.append({"raw": str(block)})
            out.append({"role": m["role"], "content": blocks})
        else:
            out.append({"role": m["role"], "content": str(content)})
    return out


def _initial_message(company_name: str, prior_verdicts: Optional[list] = None) -> str:
    """Build the first user message. Phases 2+ may pass prior verdicts so a later
    phase (e.g. Phase 3, which reasons over earlier findings instead of re-searching)
    has the actual evidence and rationale to work from."""
    if not prior_verdicts:
        return f"Company to evaluate: {company_name}"

    lines = [f"Company to evaluate: {company_name}", "", "Findings from prior phases:"]
    for v in prior_verdicts:
        lines.append(f"\n--- Phase {v.phase} ---")
        lines.append(f"Verdict: {v.verdict} (confidence {v.confidence:.2f})")
        lines.append("Rationale:")
        lines.append(v.rationale)
        searches = [tc for tc in v.tool_calls if tc["tool"] != "submit_verdict"]
        if searches:
            lines.append("Searches run:")
            for tc in searches:
                lines.append(f"  - {tc['tool']}({tc['input'].get('query', '')!r})")
    return "\n".join(lines)


def _save_run(verdict: PhaseVerdict, messages: list) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe = verdict.company.lower().replace(" ", "_").replace("/", "_")
    path = config.DATA_DIR / f"{safe}_phase{verdict.phase}_{verdict.run_id}.json"
    path.write_text(
        json.dumps(
            {
                "run_id": verdict.run_id,
                "company": verdict.company,
                "phase": verdict.phase,
                "timestamp": verdict.timestamp,
                "verdict": verdict.verdict,
                "rationale": verdict.rationale,
                "confidence": verdict.confidence,
                "tool_calls": verdict.tool_calls,
                "usage": verdict.usage,
                "messages": _serialize_messages(messages),
            },
            indent=2,
            default=str,
        )
    )


def run_phase(
    phase_number: int,
    company_name: str,
    prior_verdicts: Optional[list] = None,
) -> PhaseVerdict:
    """Run one phase of the VC funnel against a company name.

    prior_verdicts: PhaseVerdict objects from earlier phases in this run, passed
    through so a later phase (e.g. Phase 3, pure reasoning) can cite their
    findings instead of re-searching from scratch.

    Loops until Claude calls submit_verdict, then saves the full run to data/runs/.
    """
    sdk_client = anthropic.Anthropic()
    tools = _connector_tools(phase_number)
    system_prompt = PHASE_PROMPTS[phase_number]   # KeyError until prompts.py is filled in
    run_id = str(uuid.uuid4())[:8]

    messages: list = [
        {"role": "user", "content": _initial_message(company_name, prior_verdicts)}
    ]
    tool_calls_log: list = []
    verdict_input: Optional[dict] = None
    accumulated_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }

    _BACKOFF = [5, 10, 20]
    system_block = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]

    while verdict_input is None:
        for attempt, wait in enumerate([0] + _BACKOFF):
            if wait:
                time.sleep(wait)
            try:
                response = sdk_client.messages.create(
                    model=config.MODEL,
                    max_tokens=4096,
                    system=system_block,
                    tools=tools,
                    messages=messages,
                )
                break
            except anthropic.RateLimitError:
                if attempt == len(_BACKOFF):
                    raise

        u = response.usage
        accumulated_usage["input_tokens"] += u.input_tokens
        accumulated_usage["output_tokens"] += u.output_tokens
        accumulated_usage["cache_creation_input_tokens"] += getattr(u, "cache_creation_input_tokens", 0) or 0
        accumulated_usage["cache_read_input_tokens"] += getattr(u, "cache_read_input_tokens", 0) or 0
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Claude stopped without calling submit_verdict — shouldn't happen if the
            # system prompt is written correctly, but handle it so the run still saves.
            text = " ".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            verdict_input = {
                "verdict": "needs-more-info",
                "rationale": text or "Phase ended without a structured verdict.",
                "confidence": 0.0,
            }
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name == "submit_verdict":
                verdict_input = block.input
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Verdict recorded.",
                })
                tool_calls_log.append({"tool": "submit_verdict", "input": block.input})
            else:
                result_str = _call_connector(phase_number, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })
                result_data = json.loads(result_str)
                tool_calls_log.append({
                    "tool": block.name,
                    "input": block.input,
                    "result_summary": {
                        "item_count": len(result_data.get("items", [])),
                        "confidence": result_data.get("confidence"),
                        "error": result_data.get("error"),
                    },
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    verdict = PhaseVerdict(
        company=company_name,
        phase=phase_number,
        verdict=verdict_input["verdict"],
        rationale=verdict_input["rationale"],
        confidence=float(verdict_input.get("confidence", 0.0)),
        tool_calls=tool_calls_log,
        run_id=run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        usage=accumulated_usage,
    )
    _save_run(verdict, messages)
    return verdict
