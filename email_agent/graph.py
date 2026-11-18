"""Wires the LangGraph steps together.

Loop over emails:
  START -> next_email --(rule)--> apply_rule --> apply ------------------------> next_email
                      --(llm)---> classify --(label, conf >= threshold)--> apply -> next_email
                                           --(no label or lower)--> needs_decision -> next_email
                      --(done)--> print_table -> group_suggestions
Review loop (one proposal at a time, interrupt asks the user):
  group_suggestions --(proposals left)--> review_label --(proposals left)--> review_label ...
                    --(none left / [q])--> finish -> END
"""
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph

from models import State
from nodes import (apply, apply_rule, classify, decide, finish, group_suggestions, more_proposals,
                   needs_decision, next_email, print_table, review_label, route)


def build_graph():
    g = StateGraph(State)
    g.add_node("next_email", next_email)
    g.add_node("apply_rule", apply_rule)
    g.add_node("classify", classify)
    g.add_node("apply", apply)
    g.add_node("needs_decision", needs_decision)
    g.add_node("print_table", print_table)
    g.add_node("group_suggestions", group_suggestions)
    g.add_node("review_label", review_label)
    g.add_node("finish", finish)

    g.add_edge(START, "next_email")
    g.add_conditional_edges("next_email", route, {"rule": "apply_rule", "llm": "classify", "done": "print_table"})
    g.add_edge("apply_rule", "apply")
    g.add_conditional_edges("classify", decide, {"apply": "apply", "needs_decision": "needs_decision"})
    g.add_edge("apply", "next_email")
    g.add_edge("needs_decision", "next_email")
    g.add_edge("print_table", "group_suggestions")
    g.add_conditional_edges("group_suggestions", more_proposals, {"review": "review_label", "done": "finish"})
    g.add_conditional_edges("review_label", more_proposals, {"review": "review_label", "done": "finish"})
    g.add_edge("finish", END)
    # interrupt() needs a checkpointer to pause and resume; in memory is enough for one run.
    # Our Pydantic types are registered so the checkpoint may load them back.
    serde = JsonPlusSerializer(allowed_msgpack_modules=[
        ("models", "EmailSummary"), ("models", "Classification"), ("models", "Proposal"),
    ])
    return g.compile(checkpointer=InMemorySaver(serde=serde))
