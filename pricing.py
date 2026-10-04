# pricing.py
# All prices are USD per 1,000,000 tokens.
#
# ⚠ THESE NUMBERS ARE PLACEHOLDERS — I don't have verified rates for these
# models. Groq's free tier bills you nothing, but realistic numbers keep the
# cost math testable. Replace them from:
#   Groq:   https://groq.com/pricing/
#   Gemini: https://ai.google.dev/pricing
# Then run: python scripts/sync_pricing.py

import re

PRICING_LAST_VERIFIED = "unverified"

PRICING = {
    "qwen/qwen3.8-27b": {
        "input": 0.20, "output": 0.60,
        "provider": "groq", "tier": "standard",
    },

    "allam-2-7b": {
        "input": 0.05, "output": 0.15,
        "provider": "groq", "tier": "cheap",
    },

    "gemini-3.5-flash-lite": {
        "input": 0.10, "output": 0.40,
        "provider": "gemini", "tier": "cheap",
    },
    "gemini-3.8-flash": {
        "input": 0.30, "output": 2.50,
        "provider": "gemini", "tier": "standard",
    },
}


class UnknownModelError(ValueError):
    """Raised when a model has no entry in PRICING."""
    pass


# A suffix that means "same model, specific version" — safe to strip.
_VERSION_SUFFIX = re.compile(r"^-(\d{4}-\d{2}-\d{2}|\d{8}|latest|preview)$")


def normalize_model(model: str) -> str:
    """Map a provider's model string to a key in PRICING.

    Exact match wins. Otherwise a prefix match is allowed ONLY when what
    follows is a version suffix — a date, 'latest', or 'preview'. Anything
    else is a different model with different pricing.
    """
    if model in PRICING:
        return model

    for known in sorted(PRICING, key=len, reverse=True):
        if model.startswith(known):
            remainder = model[len(known):]
            if _VERSION_SUFFIX.match(remainder):
                return known

    raise UnknownModelError(f"No pricing configured for model {model!r}")


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Cost in USD for one call."""
    rates = PRICING[normalize_model(model)]
    return (
        input_tokens * rates["input"] + output_tokens * rates["output"]
    ) / 1_000_000