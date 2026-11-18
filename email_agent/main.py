"""Entry point: python email_agent/main.py [--dry-run]"""
import argparse
from uuid import uuid4

import config  # noqa: F401  (loads .env before LangSmith is used)
from langgraph.types import Command
from langsmith import Client, tracing_context
from pydantic import BaseModel

from config import PROCESSED_LABEL
from gmail_client import create_label, fetch_todays_emails, list_labels
from graph import build_graph
from models import EmailSummary
from nodes import LABELS, RULES, ModelStopped, clean_name, match_rule


def _redact(value):
    """Trace filter (runs before upload to LangSmith): rule-matched emails become id + label only,
    and recipient addresses are never uploaded."""
    if isinstance(value, BaseModel):
        value = value.model_dump()
    if isinstance(value, dict):
        if {"id", "subject", "sender", "snippet"} <= value.keys():
            email = EmailSummary(**value)
            label = match_rule(email)
            if label:
                return {"id": email.id, "rule_label": label}
            return {k: v for k, v in value.items() if k != "recipients"}
        return {k: _redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(v) for v in value]
    return value


def ask_user(p: dict) -> dict:
    """Show one proposal from the review loop and read the answer from the terminal."""
    print("\n" + "─" * 60)
    kind = "Existing label for low-confidence emails" if p["existing"] else "Proposed new label"
    print(f"{kind} {p['number']} of {p['total']}:  {p['name']}")
    print(f"Description: {p['description']}")
    print(f"Emails ({len(p['emails'])}):")
    for e in p["emails"][:10]:
        subject = " ".join((e["subject"] or "(empty)").split())[:40]
        print(f"  • {subject:<40} | {e['sender']}")
    if len(p["emails"]) > 10:
        print(f"  ... and {len(p['emails']) - 10} more")

    keys = "[a] approve   [s] skip   [q] skip all remaining" if p["existing"] else \
           "[a] approve   [r] rename   [s] skip   [q] skip all remaining"
    taken = {label.name.lower() for label in LABELS}
    while True:
        choice = input(f"{keys}  > ").strip().lower()
        if choice in ("a", "s", "q"):
            return {"action": {"a": "approve", "s": "skip", "q": "quit"}[choice]}
        if choice == "r" and not p["existing"]:
            while True:
                name = clean_name(input("New name (Enter to go back): "))
                if not name:
                    break  # back to the menu
                if name.lower() in taken:
                    print("A label with this name already exists.")
                    continue
                return {"action": "approve", "name": name}


def _gmail_label_ids(dry_run: bool) -> dict[str, str]:
    """Map every label we use to its Gmail id. Missing labels are only listed in dry-run,
    and created only in a real run (--apply)."""
    existing = {name.lower(): label_id for name, label_id in list_labels().items()}
    needed = [label.name for label in LABELS] + [PROCESSED_LABEL]
    missing = [name for name in needed if name.lower() not in existing]
    if missing:
        print(("[dry-run] would create" if dry_run else "Creating") + f" Gmail labels: {', '.join(missing)}\n")
        if not dry_run:
            for name in missing:
                existing[name.lower()] = create_label(name)
    return {name: existing[name.lower()] for name in needed if name.lower() in existing}


def main():
    parser = argparse.ArgumentParser(description="Email labeling agent (dry-run unless --apply is given)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print only, change nothing (the default)")
    mode.add_argument("--apply", action="store_true", help="really add labels in Gmail (only adds, never removes)")
    parser.add_argument("--limit", type=int, help="handle only the first N emails")
    args = parser.parse_args()
    dry_run = not args.apply
    print("[dry-run] nothing will be changed in Gmail.\n" if dry_run else "APPLY: labels will be ADDED in Gmail.\n")
    if not RULES:
        print("Note: rules.yaml not found or empty, so no emails are matched by rule.\n")

    emails = fetch_todays_emails()
    print(f"Found {len(emails)} unprocessed email(s) in the Inbox today.")
    if args.limit:
        emails = emails[: args.limit]
        print(f"--limit: handling only the first {len(emails)}.")
    print()
    if not emails:
        return
    label_ids = _gmail_label_ids(dry_run)

    client = Client(hide_inputs=_redact, hide_outputs=_redact)
    thread_id = str(uuid4())  # one run = one thread; every resume after a question continues it
    run_config = {
        # ~3 steps per email + 1 per proposal (at most one per email); explicit, never LangGraph's default
        "recursion_limit": 10 + 5 * len(emails),
        "run_name": "email-agent",
        "configurable": {"thread_id": thread_id},
        "metadata": {"thread_id": thread_id},  # groups the traces of one run in LangSmith's Threads view
    }
    try:
        with tracing_context(client=client):
            graph = build_graph()
            result = graph.invoke(
                {"dry_run": dry_run, "label_ids": label_ids, "emails": emails, "index": 0}, config=run_config
            )
            while "__interrupt__" in result:  # the graph stopped at review_label: ask, then resume
                answer = ask_user(result["__interrupt__"][0].value)
                result = graph.invoke(Command(resume=answer), config=run_config)
    except ModelStopped as e:
        done = "Nothing was changed in Gmail." if dry_run else "Emails filed before this point keep their labels."
        print(f"\nStopped: {e}\n{done}")
        raise SystemExit(1)
    finally:
        client.flush()


if __name__ == "__main__":
    main()
