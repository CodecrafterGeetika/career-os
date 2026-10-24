from __future__ import annotations

import html

import streamlit as st

CURRENT_USER = 1  # Single local profile. Replace with an authenticated user id for multi-user use.

CSS = """<style>
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1200px; }
.co-title { font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em; margin: 0; }
.co-sub { opacity: .7; margin: .15rem 0 1.2rem; }
.co-card { border: 1px solid rgba(127,127,127,.28); border-left: 4px solid #0F766E; border-radius: 10px;
  padding: .85rem 1rem; background: rgba(127,127,127,.07); margin-bottom: .6rem; }
.co-label { font-size: .85rem; opacity: .7; }
.co-value { font-size: 1.8rem; font-weight: 700; line-height: 1.2; }
.co-note { font-size: .8rem; opacity: .65; }
.co-demo { border: 1px dashed #F59E0B; background: rgba(245,158,11,.1); border-radius: 8px;
  padding: .5rem .8rem; font-size: .85rem; margin-bottom: 1rem; }
@media (max-width: 640px) { .co-title { font-size: 1.5rem; } .co-value { font-size: 1.4rem; } }
</style>"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def header(title: str, sub: str = "") -> None:
    st.markdown(f'<p class="co-title">{html.escape(title)}</p><p class="co-sub">{html.escape(sub)}</p>',
                unsafe_allow_html=True)


def metric_card(label, value, note="") -> None:
    st.markdown(f'<div class="co-card"><div class="co-label">{html.escape(str(label))}</div>'
                f'<div class="co-value">{html.escape(str(value))}</div>'
                f'<div class="co-note">{html.escape(str(note))}</div></div>', unsafe_allow_html=True)


def demo_banner() -> None:
    st.markdown('<div class="co-demo"><b>Demo data in use.</b> Items tagged [DEMO] are illustrative, not official '
                'notices. Add real opportunities from official sources, or remove demo data in Settings.</div>',
                unsafe_allow_html=True)
