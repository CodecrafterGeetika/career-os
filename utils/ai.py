"""Optional AI tips. Needs ANTHROPIC_API_KEY (env var or Streamlit secrets) and `pip install anthropic`.
Only skill names are sent, never personal details. The app is fully functional without this."""
from __future__ import annotations

import os


def ai_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def study_tips(gaps: list[str], target_role: str) -> str:
    if not ai_available():
        return "AI is not configured. Set ANTHROPIC_API_KEY to enable tips."
    try:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=os.environ.get("CAREEROS_AI_MODEL", "claude-sonnet-4-6"), max_tokens=500,
            messages=[{"role": "user", "content":
                       f"A CSE student targets '{target_role}' and lacks these skills: {', '.join(gaps) or 'none'}. "
                       "Give a concise 2-week study approach, 5 bullet points. Do not invent URLs or job notices."}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    except ImportError:
        return "Install the optional package: pip install anthropic"
    except Exception as exc:  # network/auth errors should not crash the app
        return f"AI request failed: {exc}"
