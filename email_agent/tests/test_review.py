"""The review loop (stage 4): grouping minimum, interrupt answers, Gmail + labels.yaml effects.
Everything runs with a fake model, a fake Gmail and a temporary labels.yaml."""
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import PROCESSED, FakeGmail, config, email, group, nodes, run_graph

P = "ID_" + PROCESSED


class TestReview(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.labels_file = self.dir / "labels.yaml"
        shutil.copy(config.LABELS_FILE, self.labels_file)
        self.original = self.labels_file.read_text(encoding="utf-8")
        self.saved_labels = list(nodes.LABELS)

    def tearDown(self):
        nodes.LABELS[:] = self.saved_labels  # approvals add to the in-memory list
        shutil.rmtree(self.dir)

    def run_case(self, emails, classify, groups, answers, gmail=None, dry_run=False):
        self.gmail = gmail or FakeGmail()
        asked, self.out = run_graph(emails, classify, groups, answers, self.labels_file, self.gmail, dry_run)
        return asked

    def yaml_unchanged(self):
        return self.labels_file.read_text(encoding="utf-8") == self.original

    # --- grouping minimum ---

    def test_small_group_is_not_asked_and_gets_only_processed(self):
        emails = [email("a"), email("b")]
        asked = self.run_case(emails, {"a": ("", 0.9), "b": ("", 0.9)}, [group("חדשות", ["a", "b"])], [])
        self.assertEqual(asked, 0)
        self.assertEqual(self.gmail.added, [("a", [P]), ("b", [P])])
        self.assertTrue(self.yaml_unchanged())

    def test_group_of_three_is_proposed(self):
        emails = [email("a"), email("b"), email("c")]
        asked = self.run_case(emails, {i: ("", 0.9) for i in "abc"}, [group("חדשות", ["a", "b", "c"])],
                              [{"action": "skip"}])
        self.assertEqual(asked, 1)

    # --- answers ---

    def test_skip_single_proposal_gets_only_processed(self):
        emails = [email("a"), email("b"), email("c")]
        self.run_case(emails, {i: ("", 0.9) for i in "abc"}, [group("חדשות", ["a", "b", "c"])],
                      [{"action": "skip"}])
        self.assertEqual(self.gmail.added, [("a", [P]), ("b", [P]), ("c", [P])])
        self.assertEqual(self.gmail.created, [])
        self.assertTrue(self.yaml_unchanged())

    def test_approve_new_label_creates_writes_and_applies(self):
        emails = [email("a"), email("b"), email("c")]
        self.run_case(emails, {i: ("", 0.9) for i in "abc"}, [group("חדשות", ["a", "b", "c"])],
                      [{"action": "approve"}])
        self.assertEqual(self.gmail.created, ["חדשות"])
        self.assertEqual(config.load_labels(self.labels_file)[-1].name, "חדשות")
        self.assertEqual(self.gmail.added, [(i, ["ID_חדשות", P]) for i in "abc"])

    def test_rename_uses_the_new_name(self):
        emails = [email("a"), email("b"), email("c")]
        self.run_case(emails, {i: ("", 0.9) for i in "abc"}, [group("חדשות", ["a", "b", "c"])],
                      [{"action": "approve", "name": "עדכונים"}])
        self.assertEqual(self.gmail.created, ["עדכונים"])
        self.assertEqual(config.load_labels(self.labels_file)[-1].name, "עדכונים")

    def test_existing_gmail_label_is_reused(self):
        emails = [email("a"), email("b"), email("c")]
        self.run_case(emails, {i: ("", 0.9) for i in "abc"}, [group("חדשות", ["a", "b", "c"])],
                      [{"action": "approve"}], gmail=FakeGmail(existing=["חדשות"]))
        self.assertEqual(self.gmail.created, [])
        self.assertEqual(config.load_labels(self.labels_file)[-1].name, "חדשות")

    def test_create_failure_writes_nothing(self):
        emails = [email("a"), email("b"), email("c")]
        self.run_case(emails, {i: ("", 0.9) for i in "abc"}, [group("חדשות", ["a", "b", "c"])],
                      [{"action": "approve"}], gmail=FakeGmail(create_fails=True))
        self.assertTrue(self.yaml_unchanged())
        self.assertEqual(self.gmail.added, [])  # emails left unchanged, can come up again later
        self.assertIn("1 failed", self.out)

    def test_quit_skips_this_and_all_remaining(self):
        emails = [email(i) for i in "abcdefghi"]
        groups = [group("א", list("abc")), group("ב", list("def")), group("ג", list("ghi"))]
        asked = self.run_case(emails, {i: ("", 0.9) for i in "abcdefghi"}, groups, [{"action": "quit"}])
        self.assertEqual(asked, 1)
        self.assertEqual(self.gmail.added, [(i, [P]) for i in "abcdefghi"])
        self.assertEqual(self.gmail.created, [])

    def test_low_confidence_existing_label_needs_no_minimum(self):
        emails = [email("a")]
        asked = self.run_case(emails, {"a": ("פרסומות", 0.5)}, [], [{"action": "approve"}])
        self.assertEqual(asked, 1)
        self.assertEqual(self.gmail.added, [("a", ["ID_פרסומות", P])])
        self.assertEqual(self.gmail.created, [])

    def test_dry_run_writes_nothing(self):
        emails = [email("a"), email("b"), email("c"), email("d")]
        classify = {"a": ("", 0.9), "b": ("", 0.9), "c": ("", 0.9), "d": ("פרסומות", 0.95)}
        self.run_case(emails, classify, [group("חדשות", ["a", "b", "c"])], [{"action": "approve"}], dry_run=True)
        self.assertEqual((self.gmail.created, self.gmail.added), ([], []))
        self.assertTrue(self.yaml_unchanged())
        self.assertIn("[dry-run] would create", self.out)


if __name__ == "__main__":
    unittest.main()
