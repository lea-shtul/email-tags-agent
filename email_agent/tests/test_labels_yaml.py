"""Appending a new label to labels.yaml (always on a temporary copy, never the real file)."""
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import config


class TestAppendLabel(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.file = self.dir / "labels.yaml"
        shutil.copy(config.LABELS_FILE, self.file)
        self.original = self.file.read_text(encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_appends_and_keeps_existing_text(self):
        config.append_label("קריירה", "משרות והזדמנויות - כללי", path=self.file)
        text = self.file.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(self.original))  # comments, order and old labels untouched
        labels = config.load_labels(self.file)
        self.assertEqual(labels[-1].name, "קריירה")
        self.assertEqual(labels[-1].description, "משרות והזדמנויות - כללי")
        self.assertFalse(labels[-1].rule_only)
        self.assertEqual(len(labels), len(config.load_labels(config.LABELS_FILE)) + 1)

    def test_hebrew_is_written_as_text(self):
        config.append_label("חדשות", "תיאור", path=self.file)
        self.assertIn("name: חדשות", self.file.read_text(encoding="utf-8"))

    def test_special_characters_stay_valid_yaml(self):
        config.append_label('שם: עם "מרכאות"', "תיאור - עם # ונקודתיים: כאן", path=self.file)
        self.assertEqual(config.load_labels(self.file)[-1].name, 'שם: עם "מרכאות"')

    def test_file_without_final_newline(self):
        self.file.write_text(self.original.rstrip("\n"), encoding="utf-8", newline="")
        config.append_label("חדש", "תיאור", path=self.file)
        self.assertEqual(config.load_labels(self.file)[-1].name, "חדש")

    def test_duplicate_name_is_rejected_and_file_restored(self):
        with self.assertRaises(ValueError):
            config.append_label("פרסומות", "כפילות", path=self.file)
        self.assertEqual(self.file.read_text(encoding="utf-8"), self.original)


if __name__ == "__main__":
    unittest.main()
