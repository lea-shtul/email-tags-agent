"""The no-delete guarantee: the agent can only ADD labels (and create new labels)."""
import ast
import unittest
from pathlib import Path
from unittest import mock

from helpers import config  # noqa: F401  (sets the import path)
import gmail_client

AGENT_DIR = Path(gmail_client.__file__).resolve().parent
FORBIDDEN_CALLS = {"trash", "untrash", "delete", "send", "batchModify", "batchDelete",
                   "insert", "import_", "patch", "update", "stop", "watch"}


def calls_and_keys(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    keys = {k.value for n in ast.walk(tree) if isinstance(n, ast.Dict) for k in n.keys if isinstance(k, ast.Constant)}
    return calls, keys


class TestNoDelete(unittest.TestCase):
    def test_gmail_client_has_no_destructive_calls(self):
        calls, keys = calls_and_keys(AGENT_DIR / "gmail_client.py")
        self.assertEqual(calls & FORBIDDEN_CALLS, set())
        self.assertNotIn("removeLabelIds", keys)

    def test_only_gmail_client_talks_to_gmail(self):
        for path in AGENT_DIR.glob("*.py"):
            if path.name != "gmail_client.py":
                calls, _ = calls_and_keys(path)
                self.assertNotIn("users", calls, f"{path.name} calls the Gmail API directly")

    def test_add_labels_sends_only_add_label_ids(self):
        service = mock.Mock()
        with mock.patch.object(gmail_client, "get_service", lambda: service):
            gmail_client.add_labels("m1", ["L1", "L2"])
        modify = service.users.return_value.messages.return_value.modify
        modify.assert_called_once_with(userId="me", id="m1", body={"addLabelIds": ["L1", "L2"]})


if __name__ == "__main__":
    unittest.main()
