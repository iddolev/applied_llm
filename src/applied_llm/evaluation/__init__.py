"""Evaluation: a fixed question set with gold sections, and scoring of system variants against it."""

import logging

import anthropic
from pydantic import BaseModel

log = logging.getLogger(__name__)

# Generates and validates questions, and judges answers. A different model from the
# answerer, so the answerer isn't graded by its own kind of output.
EVAL_MODEL = "claude-opus-5-5"

# USD per million input / output tokens, for cost reporting.
PRICES = {
    "claude-opus-5-5": (4.0, 20.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-haiku-5-5": (0.10, 0.50),
}


def cost(model: str, usage: dict) -> float | None:
    if model not in PRICES:
        return None
    price_in, price_out = PRICES[model]
    return (usage["input_tokens"] * price_in + usage["output_tokens"] * price_out) / 1e6


def structured_call[T: BaseModel](
    client: anthropic.Anthropic, model: str, system: str, user: str, schema: type[T], effort: str = "medium",
) -> tuple[T | None, dict]:
    """One Claude call with structured output; returns (parsed output or None if refused, usage)."""
    with client.messages.stream(
        model=model,
        max_tokens=16000,
        system=system,
        output_config={"effort": effort},
        messages=[{"role": "user", "content": user}],
        output_format=schema,
    ) as stream:
        response = stream.get_final_message()
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    if response.stop_reason == "refusal" or response.parsed_output is None:
        log.warning("No structured output (stop_reason=%s)", response.stop_reason)
        return None, usage
    return response.parsed_output, usage


def gold_matches(gold: dict, title: str, heading_path: list[str]) -> bool:
    """A gold item names an article and, optionally, a section (heading_path None = any section)."""
    return gold["title"] == title and (gold["heading_path"] is None or gold["heading_path"] == heading_path)
