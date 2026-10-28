
"""AI-powered career and study tips using the Groq API."""
from __future__ import annotations

import os


def _get_setting(name: str, default: str = "") -> str:
    """Read configuration from environment variables or Streamlit Secrets."""
    value = os.environ.get(name)
    if value:
        return value

    try:
        import streamlit as st
        value = st.secrets.get(name, default)
        return str(value) if value else default
    except Exception:
        return default


def ai_available() -> bool:
    """Check whether a Groq API key is configured."""
    return bool(_get_setting("GROQ_API_KEY"))


def study_tips(gaps: list[str], target_role: str) -> str:
    """Generate a practical two-week study plan."""
    api_key = _get_setting("GROQ_API_KEY")

    if not api_key:
        return "AI is not configured. Add GROQ_API_KEY in Streamlit Secrets."

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        model = _get_setting("GROQ_MODEL", "openai/gpt-oss-20b")

        prompt = (
            f"A CSE student is targeting '{target_role}' and needs to improve "
            f"these skills: {', '.join(gaps) or 'none specified'}. "
            "Create a practical two-week study plan in exactly 5 bullet points. "
            "Prioritize free learning resources. Do not invent URLs, job openings, "
            "or recruitment deadlines. Keep the advice beginner-friendly."
        )

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5,
        )

        content = response.choices[0].message.content
        return content.strip() if content else "AI returned an empty response."

    except ImportError:
        return "Groq package is missing. Check requirements.txt and redeploy."

    except Exception:
        return (
            "AI could not generate study tips right now. "
            "Check your Groq API key, model setting, and usage limits."
        )
