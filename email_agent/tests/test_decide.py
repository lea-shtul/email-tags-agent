"""The classify decision (conditional edge after classify)."""
import unittest

from helpers import nodes
from models import Classification


def decide(label, confidence):
    c = Classification(email_id="e", label=label, confidence=confidence)
    return nodes.decide({"results": [c]})


class TestDecide(unittest.TestCase):
    def test_at_threshold_applies(self):
        self.assertEqual(decide("פרסומות", nodes.CONFIDENCE_THRESHOLD), "apply")

    def test_just_below_threshold_needs_decision(self):
        self.assertEqual(decide("פרסומות", nodes.CONFIDENCE_THRESHOLD - 0.01), "needs_decision")

    def test_no_label_needs_decision_even_when_sure(self):
        self.assertEqual(decide("", 0.99), "needs_decision")

    def test_rule_match_routes_to_rule(self):
        e = nodes.EmailSummary(id="g", subject="s", sender="a@b.c", snippet="",
                               recipients=[nodes.RULES[0].match] if nodes.RULES else [])
        if not nodes.RULES:
            self.skipTest("rules.yaml not present")
        self.assertEqual(nodes.route({"current": e}), "rule")


if __name__ == "__main__":
    unittest.main()
