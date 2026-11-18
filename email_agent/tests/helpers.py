"""Shared test setup: import path, tracing off, a fake Gmail and a graph runner. No real API is called."""
import contextlib
import functools
import io
import os
import sys
from pathlib import Path
from unittest import mock

os.environ["LANGSMITH_TRACING"] = "false"  # tests never send traces
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # import from email_agent/

import config  # noqa: E402
import nodes  # noqa: E402
from graph import build_graph  # noqa: E402
from langgraph.types import Command  # noqa: E402
from models import Classification, EmailSummary, LabelGroup  # noqa: E402

PROCESSED = config.PROCESSED_LABEL


class FakeGmail:
    """Records every write. Labels that 'exist' in Gmail are in self.labels (name -> id)."""

    def __init__(self, existing=(), create_fails=False):
        self.labels = {name: "ID_" + name for name in existing}
        self.create_fails = create_fails
        self.created, self.added = [], []  # added: (email_id, [label ids])

    def list_labels(self):
        return dict(self.labels)

    def create_label(self, name):
        if self.create_fails:
            raise RuntimeError("fake Gmail error")
        self.created.append(name)
        self.labels[name] = "ID_" + name
        return self.labels[name]

    def add_labels(self, email_id, label_ids):
        self.added.append((email_id, list(label_ids)))


def email(i, subject="s"):
    return EmailSummary(id=i, subject=subject, sender="x@example.com", snippet="")


def run_graph(emails, classify, groups, answers, labels_file, gmail, dry_run=False):
    """Run the whole graph with a fake model and fake Gmail, answering each interrupt from `answers`.
    classify: email_id -> (label, confidence). Returns (number of questions asked, printed text)."""
    fake_classify = lambda e, labels=None: Classification(  # noqa: E731
        email_id=e.id, label=classify[e.id][0], confidence=classify[e.id][1], suggested_label="x")
    state = {"dry_run": dry_run, "label_ids": {n: "ID_" + n for n in [l.name for l in nodes.LABELS] + [PROCESSED]},
             "emails": emails, "index": 0}
    cfg = {"configurable": {"thread_id": "test"}, "recursion_limit": 200}
    out, asked = io.StringIO(), 0
    with mock.patch.object(nodes, "classify_email", fake_classify), \
         mock.patch.object(nodes, "group_emails", lambda unlabeled, sugg: groups), \
         mock.patch.object(nodes, "list_labels", gmail.list_labels), \
         mock.patch.object(nodes, "create_label", gmail.create_label), \
         mock.patch.object(nodes, "add_labels", gmail.add_labels), \
         mock.patch.object(nodes, "append_label", functools.partial(config.append_label, path=labels_file)), \
         contextlib.redirect_stdout(out):
        graph = build_graph()
        result = graph.invoke(state, cfg)
        while "__interrupt__" in result:
            result = graph.invoke(Command(resume=answers[asked]), cfg)
            asked += 1
    return asked, out.getvalue()


def group(name, ids):
    return LabelGroup(name=name, description="תיאור כללי", email_ids=ids)
