"""Pydantic data models and the graph state."""
import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel, Field


class EmailSummary(BaseModel):
    id: str
    subject: str
    sender: str
    snippet: str
    # Parsed To + Cc + List-Id addresses. Used only by rules.yaml, never sent to the model.
    recipients: list[str] = []


class Label(BaseModel):
    name: str
    description: str
    rule_only: bool = False  # True: applied only by rules.yaml, never shown to the model


class Rule(BaseModel):
    match: str  # one full group address
    label: str


class Classification(BaseModel):
    email_id: str = Field(description="The email_id given in the message")
    label: str = Field(description="Exactly one of the available label names, or an empty string if none fits")
    confidence: float = Field(ge=0, le=1, description="How sure you are about your answer, 0 to 1")
    suggested_label: str = Field(
        default="", description="Only when label is empty: a short new label name in Hebrew. Otherwise empty."
    )


class LabelGroup(BaseModel):
    """One group of unlabeled emails, as returned by the grouping model call."""
    name: str = Field(description="Short new label name in Hebrew (1-3 words)")
    description: str = Field(description="One line in Hebrew: which emails belong in this label")
    email_ids: list[str] = Field(description="The ids of the emails in this group, copied exactly")


class LabelGroups(BaseModel):
    groups: list[LabelGroup]


class Proposal(LabelGroup):
    """One item of the review loop."""
    existing: bool = False  # True: an existing label for low-confidence emails (nothing is created)


class State(TypedDict):
    dry_run: bool  # True: print only, never touch Gmail
    label_ids: dict[str, str]  # Gmail label name -> id (needed only for a real run)
    emails: list[EmailSummary]
    index: int  # position of the next email to handle
    current: EmailSummary | None
    results: Annotated[list[Classification], operator.add]
    rule_ids: Annotated[list[str], operator.add]  # ids labeled by a rule (not by the model)
    applied: Annotated[list[str], operator.add]  # ids routed to "apply"
    pending: Annotated[list[str], operator.add]  # ids routed to "needs a decision"
    # review loop (stage 4)
    proposals: list[Proposal]
    review_index: int  # position of the next proposal to review
    stop_review: bool  # set by [q]
    not_proposed: list[str]  # unlabeled emails in groups below the minimum: get only AI-Processed
    decisions: Annotated[list[str], operator.add]  # "approved" / "skipped" / "skipped_q" / "failed"
