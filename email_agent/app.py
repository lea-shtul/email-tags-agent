"""Streamlit UI for the email labeling agent (presentation layer only).

Run from the project folder:  .venv\\Scripts\\streamlit run email_agent\\app.py
"""
import streamlit as st

from ui_strings import S

st.set_page_config(page_title=S["page_title"], page_icon=":material/label:", layout="wide")

import ui_runner  # noqa: E402
import ui_views  # noqa: E402
from config import CONFIDENCE_THRESHOLD, MIN_EMAILS_PER_PROPOSAL  # noqa: E402
from demo_data import demo_emails  # noqa: E402
from ui_helpers import header, inject_css  # noqa: E402

DEMO_DEFAULT_COUNT = 20


# ---------- sidebar ----------

def _count_control(demo: bool, locked: bool) -> int | None:
    """Demo: a slider (default 20). Gmail: 'all of today's' (default) or a maximum. None means all."""
    if demo:
        total = len(demo_emails())
        return st.slider(S["count"], 1, total, min(DEMO_DEFAULT_COUNT, total), disabled=locked, key="count_demo")
    if st.toggle(S["count_all"], value=True, disabled=locked, key="count_all"):
        return None
    return st.number_input(S["count_n"], 1, 500, 10, disabled=locked, key="count_gmail")


def sidebar() -> dict:
    run = st.session_state.get("run")
    locked = run is not None and run.payload is not None  # a review is in progress
    with st.sidebar:
        st.header(S["settings"])
        source = st.segmented_control(S["source"], [S["source_demo"], S["source_gmail"]],
                                      default=S["source_demo"], disabled=locked, key="source")
        demo = source != S["source_gmail"]
        mode = st.segmented_control(S["mode"], [S["mode_dry"], S["mode_apply"]], default=S["mode_dry"],
                                    disabled=locked or demo, key="mode")
        st.caption(S["mode_demo_note"] if demo else S["login_note"])
        count = _count_control(demo, locked)

        st.divider()
        st.caption(S["thresholds"])
        st.markdown(f"{S['threshold_conf']}: **{CONFIDENCE_THRESHOLD}**  \n"
                    f"{S['threshold_min']}: **{MIN_EMAILS_PER_PROPOSAL}**")
        st.divider()
        if locked:
            st.caption(S["locked"])
            st.button(S["start_over"], icon=":material/restart_alt:", width="stretch",
                      on_click=lambda: st.session_state.update(run=None, renaming=None))
        else:
            st.button(S["run"], type="primary", icon=":material/play_arrow:", width="stretch",
                      on_click=lambda: st.session_state.update(start_requested=True, pending_apply=None))
    return {"demo": demo, "dry_run": demo or mode != S["mode_apply"], "count": count}


# ---------- running ----------

def run_agent(settings: dict, emails: list) -> None:
    """Runs the graph until the first interrupt (or the end), with live progress."""
    demo, dry_run = settings["demo"], settings["dry_run"]
    with st.status(S["running"], expanded=True) as status:
        bar = st.progress(0.0)
        seen = {"emails": 0}

        def on_step(chunk: dict) -> None:
            if "classify" in chunk or "apply_rule" in chunk:
                seen["emails"] += 1
                bar.progress(seen["emails"] / len(emails),
                             text=S["classified"].format(done=seen["emails"], total=len(emails)))
            elif "print_table" in chunk:
                bar.progress(1.0, text=S["grouping"])

        try:
            label_ids = ui_runner.demo_label_ids() if demo else ui_runner.gmail_label_ids(dry_run)
        except Exception as e:  # e.g. creating a missing label failed: nothing else runs
            status.update(label=S["run_failed"], state="error", expanded=False)
            st.session_state.fetch_error = ui_runner.describe_error(e)
            return
        run = ui_runner.start(emails, demo=demo, dry_run=dry_run, label_ids=label_ids, on_step=on_step)
        status.update(label=S["run_failed"] if run.error else S["run_done"],
                      state="error" if run.error else "complete", expanded=False)
    st.session_state.run = run


def load_emails(settings: dict) -> list | None:
    """Demo: the made-up emails. Gmail: today's unprocessed emails (read-only). None on error."""
    ui_runner.refresh_module_state(demo=settings["demo"])
    if settings["demo"]:
        return demo_emails()[: settings["count"]]
    try:
        with st.spinner(S["fetching"]):
            return ui_runner.fetch_gmail(settings["count"])
    except Exception as e:
        st.session_state.fetch_error = ui_runner.describe_error(e)
        return None


@st.dialog(S["confirm_title"])
def confirm_apply() -> None:
    """Apply mode: nothing runs until the user confirms here."""
    pending = st.session_state.pending_apply
    st.markdown(S["confirm_count"].format(n=len(pending["emails"])))
    if pending["missing"]:
        st.markdown(S["confirm_create"].format(names=", ".join(pending["missing"])))
    st.info(S["confirm_add_only"], icon=":material/add_circle:")
    st.warning(S["confirm_final"], icon=":material/warning:")
    go, cancel = st.columns(2)
    if go.button(S["confirm_go"], type="primary", width="stretch"):
        st.session_state.apply_confirmed = True
        st.rerun()
    if cancel.button(S["confirm_cancel"], width="stretch"):
        st.session_state.pending_apply = None
        st.session_state.toast = S["cancelled"]
        st.rerun()


def handle_run_request(settings: dict) -> None:
    """Called once per Run click (the flag is cleared first). Apply waits for the dialog."""
    st.session_state.start_requested = False
    st.session_state.fetch_error = None
    emails = load_emails(settings)
    if emails is None:
        return
    if not emails:
        st.session_state.fetch_error = S["no_emails"]
        return
    if settings["dry_run"]:
        run_agent(settings, emails)
        st.rerun()  # redraw once so the sidebar locks while the review is open
    try:
        missing = ui_runner.missing_labels()  # read-only, shown in the dialog
    except Exception as e:
        st.session_state.fetch_error = ui_runner.describe_error(e)
        return
    st.session_state.pending_apply = {"emails": emails, "missing": missing, "settings": settings}
    confirm_apply()


def handle_confirmed_apply() -> None:
    pending = st.session_state.pending_apply
    st.session_state.apply_confirmed = False
    st.session_state.pending_apply = None
    run_agent(pending["settings"], pending["emails"])
    st.rerun()


# ---------- page ----------

def main() -> None:
    inject_css()
    settings = sidebar()
    header(settings["demo"], settings["dry_run"])

    if st.session_state.get("apply_confirmed") and st.session_state.get("pending_apply"):
        handle_confirmed_apply()
    elif st.session_state.get("start_requested"):
        handle_run_request(settings)
    if toast := st.session_state.pop("toast", None):
        st.toast(toast, icon=":material/check_circle:")

    run = st.session_state.get("run")
    if err := st.session_state.get("fetch_error"):
        st.error(err, icon=":material/error:")
    if run is not None and run.error:
        st.error(run.error, icon=":material/error:")

    tabs = st.tabs([S["tab_overview"], S["tab_review"], S["tab_results"], S["tab_about"]])
    with tabs[0]:
        ui_views.overview(run)
    with tabs[1]:
        ui_views.review(run)
    with tabs[2]:
        ui_views.results()
    with tabs[3]:
        ui_views.about()


main()
