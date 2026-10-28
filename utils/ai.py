
"""Optional AI career and study tips using Anthropic."""
from __future__ import annotations

import os


def _get_setting(name: str, default: str = "") -> str:
    """Read a setting from environment variables or Streamlit Secrets."""
    value = os.environ.get(name)
    if value:
        return value

    try:
        import streamlit as st

        value = st.secrets.get(name, default)
        return str(value) if value else default
    except Exception:
        # Streamlit Secrets may not be configured locally.
        return default


def ai_available() -> bool:
    """Return whether an Anthropic API key is configured."""
    return bool(_get_setting("ANTHROPIC_API_KEY"))


def study_tips(gaps: list[str], target_role: str) -> str:
    """Generate a concise two-week study plan."""
    api_key = _get_setting("ANTHROPIC_API_KEY")

    if not api_key:
        return "AI is not configured yet. Add ANTHROPIC_API_KEY in Streamlit Secrets."

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        model = _get_setting("CAREEROS_AI_MODEL", "claude-sonnet-4-6")

        prompt = (
            f"A CSE student targets '{target_role}' and lacks these skills: "
            f"{', '.join(gaps) or 'none'}. "
            "Give a concise, practical two-week study plan in exactly 5 bullet points. "
            "Prioritize free resources where possible. Do not invent URLs or job notices."
        )

        message = client.messages.create(
            model=model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        return "\n".join(
            block.text
            for block in message.content
            if getattr(block, "type", "") == "text"
        ) or "AI returned an empty response. Please try again."

    except ImportError:
        return "The Anthropic package is missing. Check requirements.txt and redeploy."

    except Exception:
        # Avoid showing technical details or credentials to users.
        return (
            "AI could not generate tips right now. "
            "Please check the API key, model setting, and API account, then try again."
        )
