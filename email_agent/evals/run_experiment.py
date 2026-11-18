"""Run the classifier over the dataset in LangSmith.

Usage: python email_agent/evals/run_experiment.py --name baseline
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # import from email_agent/

import config  # noqa: E402,F401  (loads .env)
from langsmith import Client, evaluate  # noqa: E402

from dataset import DATASET_NAME, upload  # noqa: E402
from evaluators import confident_match, label_match  # noqa: E402
from models import EmailSummary  # noqa: E402
from nodes import ModelStopped, classify_email  # noqa: E402

REPETITIONS = 3  # each email is classified 3 times; the model has no temperature setting
stopped = ""  # set on the first rate-limit/quota error; later examples skip the model


def target(inputs: dict) -> dict:
    global stopped
    if stopped:
        raise ModelStopped(stopped)
    email = EmailSummary(id=inputs["email_id"], sender=inputs["sender"],
                         subject=inputs["subject"], snippet=inputs["snippet"])
    try:
        c = classify_email(email)
    except ModelStopped as e:
        stopped = str(e)
        raise
    return {"label": c.label, "confidence": c.confidence, "suggested_label": c.suggested_label}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="experiment name, e.g. baseline")
    args = parser.parse_args()

    client = Client()
    upload(client)
    results = evaluate(
        target, data=DATASET_NAME, evaluators=[label_match, confident_match], experiment_prefix=args.name,
        metadata={"model": config.MODEL_NAME}, max_concurrency=1, num_repetitions=REPETITIONS, client=client,
    )

    if stopped:
        print(f"\nExperiment stopped: {stopped}")
        print(f"Results of '{results.experiment_name}' are incomplete. Delete it in LangSmith and run again later.")
        raise SystemExit(1)

    # group the repetitions by email
    by_email = defaultdict(list)
    for r in results:
        out = r["run"].outputs or {}
        scores = {e.key: e.score for e in r["evaluation_results"]["results"]}
        by_email[r["example"].inputs["email_id"]].append((r["example"].outputs["label"], out, scores))

    print(f"\nEmails wrong or below {config.CONFIDENCE_THRESHOLD} confidence in at least one of {REPETITIONS} runs:")
    print(f"{'id':<9} {'expected':<16} answers (label / confidence)")
    for email_id in sorted(by_email):
        runs = by_email[email_id]
        if all(s["confident_match"] for _, _, s in runs):
            continue
        answers = ", ".join(f"{o.get('label') or 'none'} / {o.get('confidence', 0):.2f}" for _, o, _ in runs)
        print(f"{email_id:<9} {runs[0][0]:<16} {answers}")

    all_scores = [s for runs in by_email.values() for _, _, s in runs]
    print(f"\nExperiment '{results.experiment_name}' ({len(by_email)} emails x {REPETITIONS} runs):")
    for key in ("label_match", "confident_match"):
        print(f"  {key:<16} average = {sum(s[key] for s in all_scores) / len(all_scores):.1%}")


if __name__ == "__main__":
    main()
