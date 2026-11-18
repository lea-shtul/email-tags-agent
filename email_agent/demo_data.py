"""Made-up emails for the UI demo mode: the evals dataset plus a few clearly fake extras.
No real names, addresses or data. Rule matches use the fake addresses of rules.example.yaml."""
from pathlib import Path

import yaml

from evals.dataset import EMAILS  # (sender, subject, snippet, expected label) - reused unchanged
from models import EmailSummary, Rule

EXAMPLE_RULES_FILE = Path(__file__).parent / "rules.example.yaml"

# (id, sender, subject, snippet, recipients)
EXTRAS = [
    ("extra-1", "מתכנתת מהקורס <dev.student@example.com>", "שאלה על התרגיל ב-React",
     "מישהי הצליחה להריץ את השרת? אני מקבלת שגיאה על פורט 3000.", ["programming-group@example.com"]),
    ("extra-2", "ועדת השנתון <yearbook.team@example.com>", "תזכורת: להעלות תמונות עד יום חמישי",
     "מי שעוד לא העלתה תמונות לשנתון - הקישור בפנים.", ["yearbook-group@example.com"]),
    ("extra-3", "נציגת הכיתה <class.rep@example.com>", "טיול שנתי - פרטים ואישור הורים",
     "מצורף טופס אישור. יש להחזיר עד יום ראשון.", ["class-group@example.com"]),
    ("extra-4", "נועה <noa.friend@example.com>", "Re: מחר בערב",
     "מעולה, אני מביאה את העוגה. נתראה בשמונה.", []),
    ("extra-5", "תמר <tamar.family@example.com>", "",
     "קנית כבר את המתנה ליום ההולדת? תתקשרי כשאת מתפנה.", []),
]

# 1-based positions in the evals dataset to show first: private, receipts, sponsored newsletters,
# borderline, then a few confident ones. The rest follow in dataset order.
FIRST = [16, 17, 28, 35, 36, 18, 26, 31, 20, 30, 1, 6, 11, 21, 24]


def demo_emails() -> list[EmailSummary]:
    extras = [EmailSummary(id=i, sender=s, subject=subj, snippet=snip, recipients=r)
              for i, s, subj, snip, r in EXTRAS]
    order = FIRST + [n for n in range(1, len(EMAILS) + 1) if n not in FIRST]
    dataset = [EmailSummary(id=f"fake-{n:02d}", sender=EMAILS[n - 1][0], subject=EMAILS[n - 1][1],
                            snippet=EMAILS[n - 1][2]) for n in order]
    return extras + dataset


def demo_rules() -> list[Rule]:
    """The fake group addresses, used instead of the real rules.yaml in demo mode."""
    return [Rule(**item) for item in yaml.safe_load(EXAMPLE_RULES_FILE.read_text(encoding="utf-8"))]
