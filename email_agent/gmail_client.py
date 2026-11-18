"""All Gmail API calls, nothing else.

Safety: the only calls that change Gmail are labels().create (new label) and
messages().modify with addLabelIds only. Nothing here removes labels, deletes, trashes,
archives, moves or sends.
"""
import html
from datetime import datetime
from email.utils import getaddresses
from functools import cache

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, GMAIL_SCOPE, PROCESSED_LABEL, TOKEN_FILE
from models import EmailSummary


@cache
def get_service():
    """Log in with OAuth (browser on first run) and return a Gmail API client."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), [GMAIL_SCOPE])
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), [GMAIL_SCOPE])
        creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def _local_midnight_epoch() -> int:
    """Seconds since epoch for today 00:00 in this computer's time zone."""
    now = datetime.now().astimezone()
    return int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def fetch_todays_emails() -> list[EmailSummary]:
    """Return Inbox emails received since local midnight (all pages), skipping already processed ones."""
    service = get_service()
    query = f"in:inbox after:{_local_midnight_epoch()} -label:{PROCESSED_LABEL}"

    ids: list[str] = []
    page_token = None
    while True:
        resp = service.users().messages().list(
            userId="me", q=query, pageToken=page_token, maxResults=100
        ).execute()
        ids += [m["id"] for m in resp.get("messages", [])]
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    emails = []
    for msg_id in ids:
        msg = service.users().messages().get(
            userId="me", id=msg_id, format="metadata",
            metadataHeaders=["Subject", "From", "To", "Cc", "List-Id"],
        ).execute()
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        emails.append(EmailSummary(
            id=msg_id,
            subject=headers.get("subject", "(no subject)"),
            sender=headers.get("from", "(unknown sender)"),
            snippet=html.unescape(msg.get("snippet", "")),
            recipients=_recipients(headers),
        ))
    return emails


def list_labels() -> dict[str, str]:
    """Label name -> label id for all labels in the mailbox (read-only)."""
    labels = get_service().users().labels().list(userId="me").execute().get("labels", [])
    return {label["name"]: label["id"] for label in labels}


def create_label(name: str) -> str:
    """Create a new label and return its id."""
    body = {"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    return get_service().users().labels().create(userId="me", body=body).execute()["id"]


def add_labels(message_id: str, label_ids: list[str]) -> None:
    """ADD labels to one email. Never sends removeLabelIds, so nothing is removed or moved."""
    get_service().users().messages().modify(
        userId="me", id=message_id, body={"addLabelIds": label_ids}
    ).execute()


def _recipients(headers: dict[str, str]) -> list[str]:
    """Lower-case addresses from To + Cc, plus the List-Id of a Google Group as an address."""
    addrs = [a.lower() for _, a in getaddresses([headers.get("to", ""), headers.get("cc", "")]) if a]
    list_id = headers.get("list-id", "")  # looks like: Group name <my-group.googlegroups.com>
    if "<" in list_id:
        lid = list_id.split("<")[-1].rstrip("> ").strip().lower()
        if lid.endswith(".googlegroups.com"):
            addrs.append(lid.removesuffix(".googlegroups.com") + "@googlegroups.com")
    return addrs
