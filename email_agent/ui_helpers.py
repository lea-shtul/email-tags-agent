"""Small visual helpers for the UI: CSS (the only custom CSS, kept here), RTL text, colors, banners."""
import html

import streamlit as st

from ui_strings import S

# Badge colors per label (st.badge color names) and the matching text colors for the table.
LABEL_COLORS = {"טכנולוגיה": "blue", "פרסומות": "orange", "אבטחה וחשבונות": "red", "רשתות חברתיות": "violet"}
HEX = {"blue": "#2563EB", "orange": "#C2410C", "red": "#B91C1C", "violet": "#7C3AED",
       "gray": "#475569", "green": "#15803D"}

CSS = """
/* The font (Heebo) and colors come from .streamlit/config.toml. Only what the theme cannot do is here. */

/* Hebrew / mixed text: direction from the first strong character, aligned to its start */
.rtl { unicode-bidi: plaintext; text-align: start; }
.card-title { font-size: 1.45rem; font-weight: 600; margin: 0.25rem 0 0.15rem 0; }
.card-desc { color: #475569; margin-bottom: 0.5rem; }
.email-line { padding: 0.35rem 0; border-bottom: 1px solid #E2E8F0; }
.email-line:last-child { border-bottom: none; }
.email-sender { color: #64748B; font-size: 0.9rem; }
.subtitle { color: #64748B; font-size: 1.05rem; margin-top: -0.6rem; margin-bottom: 1rem; }
"""


def inject_css() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def rtl(text: str, cls: str = "") -> str:
    """HTML for text that may be Hebrew, English or mixed: dir="auto" picks the direction."""
    return f'<div dir="auto" class="rtl {cls}">{html.escape(text)}</div>'


def isolate(text: str) -> str:
    """For st.dataframe (drawn on a canvas, CSS does not reach it): Unicode first-strong isolate,
    so each cell takes its direction from its own first letter."""
    return f"⁨{text}⁩" if text else text


def label_color(name: str) -> str:
    return LABEL_COLORS.get(name, "gray")


def label_style(value: str) -> str:
    return f"color: {HEX[label_color(value)]}; font-weight: 600" if value and value != "-" else "color: #94A3B8"


def route_style(value: str) -> str:
    return f"color: {HEX['green' if value == S['route_apply'] else 'orange']}; font-weight: 600"


def graph_dot(graph) -> str:
    """Graphviz DOT for st.graphviz_chart, built from LangGraph's own description of the compiled graph
    (nodes, edges, and which edges are conditional). Rendered in the browser, no extra package."""
    g = graph.get_graph()
    lines = [
        "digraph {", 'rankdir=TB; bgcolor="transparent"; nodesep=0.35; ranksep=0.4;',
        'node [shape=box, style="rounded,filled", fillcolor="#EEF2F7", color="#CBD5E1", '
        'fontname="Heebo", fontsize=11, fontcolor="#1E293B"];',
        'edge [color="#64748B", fontname="Heebo", fontsize=9, fontcolor="#475569"];',
    ]
    for node_id in g.nodes:
        if node_id in ("__start__", "__end__"):
            lines.append(f'"{node_id}" [label="{node_id.strip("_")}", shape=oval, fillcolor="#3F5BA9", '
                         'fontcolor="white", color="#3F5BA9"];')
        elif node_id == "review_label":
            lines.append(f'"{node_id}" [label="review_label\\n(interrupt)", fillcolor="#E0E7FF", color="#3F5BA9"];')
    for e in g.edges:
        style = "dashed" if e.conditional else "solid"
        label = f', label=" {e.data}"' if e.data and e.data != e.target else ""
        lines.append(f'"{e.source}" -> "{e.target}" [style={style}{label}];')
    return "\n".join(lines + ["}"])


def header(demo: bool, dry_run: bool) -> None:
    st.title(S["title"])
    st.markdown(f'<div class="subtitle">{html.escape(S["subtitle"])}</div>', unsafe_allow_html=True)
    if demo:
        st.badge(S["demo_badge"], icon=":material/science:", color="violet")
    if dry_run:
        st.info(S["banner_dry"], icon=":material/visibility:")
    else:
        st.warning(S["banner_apply"], icon=":material/warning:")
