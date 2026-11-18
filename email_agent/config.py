"""Project settings and the loaders for labels.yaml / rules.yaml."""
from pathlib import Path

import yaml
from dotenv import load_dotenv

from models import Label, Rule

# Project root = the folder above email_agent/. Secrets live there (all in .gitignore).
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CREDENTIALS_FILE = ROOT / "credentials.json"
TOKEN_FILE = ROOT / "token.json"
LABELS_FILE = Path(__file__).parent / "labels.yaml"
RULES_FILE = Path(__file__).parent / "rules.yaml"  # real group addresses, in .gitignore

# gmail.modify: read emails and add labels. The code never deletes, trashes, archives or sends.
# After changing the scope, delete token.json and log in again.
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.modify"

MODEL_NAME = "claude-haiku-5-5"
PROCESSED_LABEL = "AI-Processed"
CONFIDENCE_THRESHOLD = 0.7
MIN_EMAILS_PER_PROPOSAL = 3  # smaller groups of unlabeled emails are not proposed (and not marked)


def load_labels(path: Path = LABELS_FILE) -> list[Label]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return [Label(**item) for item in data]


def label_yaml_entry(name: str, description: str) -> str:
    """The YAML text for one new label, ready to append to labels.yaml (Hebrew kept as is)."""
    entry = [{"name": name, "description": description, "rule_only": False}]
    return yaml.safe_dump(entry, allow_unicode=True, sort_keys=False, width=1000)


def append_label(name: str, description: str, path: Path = LABELS_FILE) -> None:
    """Append one label to the end of labels.yaml (comments and order kept), then reload to check
    the file is still valid and has the label exactly once. On any problem the old text is restored."""
    before = path.read_text(encoding="utf-8")
    separator = "" if not before or before.endswith("\n") else "\n"
    path.write_text(before + separator + label_yaml_entry(name, description), encoding="utf-8", newline="")
    try:
        if [label.name for label in load_labels(path)].count(name) != 1:
            raise ValueError(f"label '{name}' is not in labels.yaml exactly once")
    except Exception:
        path.write_text(before, encoding="utf-8", newline="")
        raise


def load_rules(labels: list[Label]) -> list[Rule]:
    """Load rules.yaml (empty list if missing). Every rule label must be a rule_only label."""
    if not RULES_FILE.exists():
        return []
    rules = [Rule(**item) for item in yaml.safe_load(RULES_FILE.read_text(encoding="utf-8")) or []]
    rule_only = {label.name for label in labels if label.rule_only}
    for rule in rules:
        if rule.label not in rule_only:
            raise SystemExit(f"rules.yaml: label '{rule.label}' must exist in labels.yaml with rule_only: true")
    return rules
