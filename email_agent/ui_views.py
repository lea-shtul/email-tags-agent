"""The tabs of the UI. Everything shown is read from the graph state; no agent logic lives here."""
from collections import Counter

import pandas as pd
import streamlit as st

import nodes
import ui_runner
from graph import build_graph
from nodes import clean_name
from ui_helpers import graph_dot, isolate, label_color, label_style, route_style, rtl
from ui_strings import S

# Experiment results on dataset email-labels-v2 (39 emails x 3 repetitions), copied from LangSmith.
# (short name, LangSmith experiment, label_match %, confident_match %, what changed)
EXPERIMENTS = [
    ("baseline", "baseline-1bd54353", 88.9, 78.6,
     "The original classification prompt."),
    ("attempt 1", "after-improvement-4a0cdb43", 86.3, 82.9,
     "Added one rule: decide by the TYPE of the email, not by its sender or topic."),
    ("attempt 2", "after-improvement-v2-8ddb6462", 97.4, 89.7,
     "Refined the same rule: event invitations follow their topic; receipts and shipping notices are not ads."),
]


# ---------- Overview ----------

def _rows(run) -> list[dict]:
    v = run.values
    emails = {e.id: e for e in v.get("emails", [])}
    rule_ids, applied = set(v.get("rule_ids", [])), set(v.get("applied", []))
    return [{
        S["col_subject"]: isolate(" ".join((emails[c.email_id].subject or S["empty_subject"]).split())),
        S["col_label"]: c.label or "-",
        S["col_conf"]: c.confidence,
        S["col_suggested"]: isolate(c.suggested_label) or "-",
        S["col_via"]: "rule" if c.email_id in rule_ids else "llm",
        S["col_route"]: S["route_apply"] if c.email_id in applied else S["route_decision"],
    } for c in v.get("results", [])]


def overview(run) -> None:
    if run is None:
        st.info(S["empty"], icon=":material/play_circle:")
        return
    rows = _rows(run)
    if not rows:
        return
    v = run.values
    by_rule = len(v.get("rule_ids", []))
    source = S["source_demo"] if run.demo else S["source_gmail"]
    mode = S["mode_dry"] if run.dry_run else S["mode_apply"]
    st.caption(S["showing"].format(source=source, mode=mode, n=len(run.emails)))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(S["kpi_found"], len(v.get("emails", [])), border=True)
    k2.metric(S["kpi_rule"], by_rule, border=True)
    k3.metric(S["kpi_model"], len(v.get("applied", [])) - by_rule, border=True)
    k4.metric(S["kpi_waiting"], len(v.get("pending", [])), border=True)
    if run.payload:
        st.info(S["go_review"], icon=":material/rate_review:")

    left, right = st.columns([2, 5], gap="large")
    with left:
        st.subheader(S["per_label"])
        counts = Counter(r[S["col_label"]] if r[S["col_label"]] != "-" else S["no_label"] for r in rows)
        chart = pd.DataFrame({"label": list(counts), "emails": list(counts.values())}).sort_values("emails")
        st.bar_chart(chart, x="label", y="emails", horizontal=True, x_label="", y_label="", height=320)
    with right:
        st.subheader(S["all_emails"])
        df = pd.DataFrame(rows)
        styled = df.style.map(label_style, subset=[S["col_label"]]).map(route_style, subset=[S["col_route"]])
        st.dataframe(styled, hide_index=True, height=420, column_config={
            S["col_subject"]: st.column_config.TextColumn(width="large"),
            S["col_conf"]: st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f", width="small"),
        })


# ---------- Review ----------

def _answer(answer: dict, interrupt_id: str, toast: str) -> None:
    """Button callback: resume the graph with exactly the terminal's answer values."""
    if ui_runner.resume(st.session_state.run, answer, interrupt_id):
        st.session_state.toast = toast
    st.session_state.renaming = None


def _proposal_card(run) -> None:
    p, iid = run.payload, run.interrupt_id
    st.progress(p["number"] / p["total"], text=S["review_progress"].format(i=p["number"], n=p["total"]))
    with st.container(border=True):
        if p["existing"]:
            st.badge(S["type_existing"], icon=":material/label:", color=label_color(p["name"]))
        else:
            st.badge(S["type_new"], icon=":material/new_label:", color="primary")
        st.markdown(rtl(p["name"], "card-title") + rtl(p["description"], "card-desc"), unsafe_allow_html=True)
        with st.expander(S["emails_in"].format(n=len(p["emails"]))):
            st.markdown("".join(
                f'<div class="email-line">{rtl(e["subject"] or S["empty_subject"])}'
                f'{rtl(e["sender"], "email-sender")}</div>' for e in p["emails"]), unsafe_allow_html=True)
        if st.session_state.get("renaming") == iid:
            _rename_form(run, p, iid)
        else:
            _buttons(p, iid)


def _buttons(p: dict, iid: str) -> None:
    cols = st.columns(4 if not p["existing"] else 3)
    name = p["name"]
    cols[0].button(S["approve"], type="primary", icon=":material/check:", width="stretch", on_click=_answer,
                   args=({"action": "approve"}, iid, S["toast_approve"].format(name=name)), key=f"a-{iid}")
    if not p["existing"]:
        cols[1].button(S["rename"], icon=":material/edit:", width="stretch", key=f"r-{iid}",
                       on_click=lambda: st.session_state.update(renaming=iid))
    cols[-2].button(S["skip"], icon=":material/skip_next:", width="stretch", on_click=_answer,
                    args=({"action": "skip"}, iid, S["toast_skip"].format(name=name)), key=f"s-{iid}")
    cols[-1].button(S["skip_all"], icon=":material/fast_forward:", width="stretch", on_click=_answer,
                    args=({"action": "quit"}, iid, S["toast_quit"]), key=f"q-{iid}")


def _rename_form(run, p: dict, iid: str) -> None:
    """Same checks as the terminal: tags stripped, not empty, not an existing label name."""
    with st.form(f"rename-{iid}", border=False):
        raw = st.text_input(S["new_name"], value=p["name"])
        save_col, cancel_col = st.columns(2)
        save = save_col.form_submit_button(S["save_name"], type="primary", width="stretch")
        cancel = cancel_col.form_submit_button(S["cancel"], width="stretch")
    if cancel:
        st.session_state.renaming = None
        st.rerun()
    if save:
        name = clean_name(raw)
        if not name:
            st.error(S["name_empty"])
        elif name.lower() in {label.name.lower() for label in nodes.LABELS}:
            st.error(S["name_taken"])
        else:
            _answer({"action": "approve", "name": name}, iid, S["toast_approve"].format(name=name))
            st.rerun()


def _summary(run) -> None:
    v = run.values
    d = v.get("decisions", [])
    st.subheader(S["summary"])
    if not v.get("proposals"):
        st.caption(S["nothing_to_review"])
    items = [(S["sum_approved"], d.count("approved")), (S["sum_skipped"], d.count("skipped")),
             (S["sum_quit"], d.count("skipped_q")), (S["sum_small"], len(v.get("not_proposed") or []))]
    if "failed" in d:
        items.append((S["sum_failed"], d.count("failed")))
    for col, (label, value) in zip(st.columns(len(items)), items):
        col.metric(label, value, border=True)
    if run.dry_run:
        st.caption(S["dry_note"])


def review(run) -> None:
    if run is None:
        st.info(S["no_review"], icon=":material/rate_review:")
        return
    st.subheader(S["review_title"])
    if run.payload:
        _proposal_card(run)
    elif run.done:
        _summary(run)


# ---------- Results ----------

def results() -> None:
    st.subheader(S["results_title"])
    st.markdown(S["results_intro"])
    base_lm, base_cm = EXPERIMENTS[0][2], EXPERIMENTS[0][3]
    for col, (name, experiment, lm, cm, change) in zip(st.columns(3), EXPERIMENTS):
        with col.container(border=True):
            st.markdown(f"**{name}**  \n:gray[{experiment}]")
            delta = None if name == "baseline" else f"{lm - base_lm:+.1f} pts {S['vs_baseline']}"
            st.metric(S["metric_lm"], f"{lm}%", delta)
            delta = None if name == "baseline" else f"{cm - base_cm:+.1f} pts {S['vs_baseline']}"
            st.metric(S["metric_cm"], f"{cm}%", delta)
            st.caption(change)
    chart = pd.DataFrame({"experiment": [e[0] for e in EXPERIMENTS],
                          S["metric_lm"]: [e[2] for e in EXPERIMENTS],
                          S["metric_cm"]: [e[3] for e in EXPERIMENTS]})
    st.bar_chart(chart, x="experiment", y=[S["metric_lm"], S["metric_cm"]], stack=False,
                 color=["#3F5BA9", "#94A3B8"], y_label="%", x_label="", height=320, sort=False)
    st.caption(S["results_caveat"])


# ---------- About ----------

def about() -> None:
    st.subheader(S["about_title"])
    st.markdown(S["about_text"])
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"#### {S['about_graph']}")
        st.graphviz_chart(graph_dot(build_graph()), width="stretch")
        st.caption(S["about_graph_note"])
    with right:
        st.markdown(f"#### {S['about_safety']}")
        with st.container(border=True):
            st.markdown("\n".join(f"- {line}" for line in S["safety"]))
