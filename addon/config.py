import re
from dataclasses import dataclass

from aqt import mw

CLOZE_START_RE = re.compile(r"\{\{c\d+::", re.IGNORECASE)
DEFAULT_REPLACEMENT = "} }"


@dataclass(frozen=True)
class ParsedCloze:
    opening: str
    answer: str
    hint: str | None
    end: int


@dataclass(frozen=True)
class RewriteTokens:
    replacement: str
    boundary_replacement: str


def addon_config() -> dict:
    config = mw.addonManager.getConfig(__name__) or {}
    if isinstance(config, dict):
        return config
    return {}


def is_valid_replacement(value) -> bool:
    return isinstance(value, str) and bool(value) and "}}" not in value


def replacement_token() -> str:
    replacement = addon_config().get("replacement", DEFAULT_REPLACEMENT)
    if is_valid_replacement(replacement):
        return replacement
    return DEFAULT_REPLACEMENT


def rewrite_tokens() -> RewriteTokens:
    replacement = replacement_token()
    boundary_replacement = replacement if replacement.endswith("}") else DEFAULT_REPLACEMENT
    return RewriteTokens(
        replacement=replacement,
        boundary_replacement=boundary_replacement,
    )


def remove_nbsp_in_mathjax() -> bool:
    return bool(addon_config().get("remove_nbsp_in_mathjax", True))
