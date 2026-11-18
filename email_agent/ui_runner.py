"""Drives the existing LangGraph graph for the UI: start, stream progress, stop at interrupt, resume.
Nothing here changes the agent's logic; it calls the same graph, privacy filter and answers as main.py."""
import contextlib
import io
from dataclasses import dataclass, field
from unittest import mock
from uuid import uuid4

from googleapiclient.errors import HttpError
from langgraph.errors import GraphRecursionError
from langgraph.types import Command
from langsmith import Client, tracing_context

import gmail_client
import nodes
from config import PROCESSED_LABEL, load_labels, load_rules
from demo_data import demo_rules
from graph import build_graph
from main import _gmail_label_ids, _redact
from nodes import ModelStopped
from ui_strings import S


@dataclass
class Run:
    """One agent run, kept in st.session_state between Streamlit reruns."""
    demo: bool
    dry_run: bool
    emails: list
    graph: object
    config: dict
    client: Client
    payload: dict | None = None  # the proposal waiting for an answer
    interrupt_id: str | None = None
    values: dict = field(default_factory=dict)  # latest graph state
    done: bool = False
    error: str | None = None


def refresh_module_state(demo: bool) -> None:
    """Reload labels and rules in place: the Streamlit process lives on between runs, while the
    terminal agent loads them once per run. In demo the fake rules of rules.example.yaml are used."""
    labels = load_labels()
    nodes.LABELS[:] = labels
    nodes.LLM_LABELS[:] = [label for label in labels if not label.rule_only]  # same list classify_email uses
    nodes.RULES[:] = demo_rules() if demo else load_rules(labels)


@contextlib.contextmanager
def no_gmail(demo: bool):
    """Demo mode must never reach Gmail: list_labels answers 'no labels', every other call fails loudly."""
    if not demo:
        yield
        return

    def blocked(*args, **kwargs):
        raise RuntimeError("Demo mode tried to call Gmail")

    with mock.patch.object(nodes, "list_labels", lambda: {}), \
         mock.patch.object(nodes, "create_label", blocked), \
         mock.patch.object(nodes, "add_labels", blocked), \
         mock.patch.object(gmail_client, "get_service", blocked):
        yield


def demo_label_ids() -> dict[str, str]:
    """Placeholder ids so dry-run steps that look up a label id work; they are never sent anywhere."""
    return {name: f"demo-{name}" for name in [label.name for label in nodes.LABELS] + [PROCESSED_LABEL]}


# ---- Gmail source (all calls go through the existing gmail_client / main functions) ----

def fetch_gmail(limit: int | None) -> list:
    """Today's unprocessed Inbox emails (read-only), cut to `limit` like --limit."""
    emails = gmail_client.fetch_todays_emails()
    return emails[:limit] if limit else emails


def missing_labels() -> list[str]:
    """Labels the agent uses that do not exist in Gmail yet (read-only)."""
    existing = {name.lower() for name in gmail_client.list_labels()}
    needed = [label.name for label in load_labels()] + [PROCESSED_LABEL]
    return [name for name in needed if name.lower() not in existing]


def gmail_label_ids(dry_run: bool) -> dict[str, str]:
    """The same function main.py uses: in a real run it creates the missing labels."""
    with contextlib.redirect_stdout(io.StringIO()):
        return _gmail_label_ids(dry_run)


def describe_error(e: Exception) -> str:
    """A clear message for errors that happen outside the graph (Gmail login, reading emails)."""
    if isinstance(e, HttpError):
        return S["err_gmail"].format(detail=getattr(e, "status_code", "") or type(e).__name__)
    if isinstance(e, FileNotFoundError):
        return S["err_credentials"]
    if type(e).__name__ in ("RefreshError", "InvalidGrantError"):
        return S["err_login"]
    return S["err_other"].format(detail=f"{type(e).__name__}: {e}")


def start(emails: list, demo: bool, dry_run: bool, label_ids: dict, on_step=None) -> Run:
    thread_id = str(uuid4())
    run = Run(
        demo=demo, dry_run=dry_run, emails=emails, graph=build_graph(),
        client=Client(hide_inputs=_redact, hide_outputs=_redact),  # the same privacy filter as main.py
        config={
            "recursion_limit": 10 + 5 * len(emails),  # same formula as main.py
            "run_name": "email-agent",
            "configurable": {"thread_id": thread_id},
            "metadata": {"thread_id": thread_id, "ui": True, "demo": demo},
        },
    )
    _stream(run, {"dry_run": dry_run, "label_ids": label_ids, "emails": emails, "index": 0}, on_step)
    return run


def resume(run: Run, answer: dict, interrupt_id: str) -> bool:
    """Resume only the interrupt that is really waiting (protects against double clicks)."""
    if run.payload is None or run.interrupt_id != interrupt_id:
        return False
    _stream(run, Command(resume=answer))
    return True


def _stream(run: Run, graph_input, on_step=None) -> None:
    run.payload = run.interrupt_id = None
    try:
        with no_gmail(run.demo), tracing_context(client=run.client), contextlib.redirect_stdout(io.StringIO()):
            for chunk in run.graph.stream(graph_input, run.config, stream_mode="updates"):
                if "__interrupt__" in chunk:
                    interrupt = chunk["__interrupt__"][0]
                    run.payload, run.interrupt_id = interrupt.value, interrupt.id
                elif on_step:
                    on_step(chunk)
    except ModelStopped as e:
        run.error = str(e)
    except GraphRecursionError:
        run.error = S["err_recursion"]
    except Exception as e:  # Gmail and anything else: a clear message, never a crash
        run.error = describe_error(e)
    if run.error and not run.dry_run:
        run.error += " " + S["err_apply_note"]
    run.values = run.graph.get_state(run.config).values
    run.done = run.payload is None and run.error is None
    run.client.flush()
