"""Dataset CLI routing, separate from prediction and serving."""

import json
from pathlib import Path

from .dataset import (
    DEFAULT_QUESTIONS,
    DEFAULT_REVIEWS,
    DEFAULT_SOURCE,
    append_review,
    freeze,
    load_workspace,
    review_packet,
    validation_summary,
)
from .schemas import Cause


def add_dataset_commands(commands):
    dataset = commands.add_parser("dataset", help="Author, review, and freeze a local dataset")
    actions = dataset.add_subparsers(dest="dataset_command", required=True)
    for name in ("validate", "review-packet", "review", "freeze"):
        action = actions.add_parser(name)
        action.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
        action.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
        action.add_argument("--reviews", type=Path, default=DEFAULT_REVIEWS)
        if name in ("review-packet", "freeze"):
            action.add_argument("--output", type=Path, required=True)
        if name == "review":
            action.add_argument("--example-id", required=True)
            action.add_argument("--decision", choices=["approved", "rejected"], required=True)
            action.add_argument("--label", type=Cause, choices=list(Cause))
            action.add_argument("--reviewer", required=True)
            action.add_argument("--note", required=True)


def run_dataset_command(args) -> int:
    if args.dataset_command == "review":
        event = append_review(
            source=args.source,
            questions=args.questions,
            reviews=args.reviews,
            example_id=args.example_id,
            decision=args.decision,
            label=args.label,
            reviewer=args.reviewer,
            notes=args.note,
        )
        print(event.model_dump_json(indent=2))
        return 0
    workspace = load_workspace(args.source, args.questions, args.reviews)
    if args.dataset_command == "validate":
        summary = validation_summary(workspace)
        print(json.dumps(summary, indent=2))
        return 0 if summary["valid"] else 2
    if args.dataset_command == "review-packet":
        # Refuse output aliases to inputs; preserve the append-only log and source records.
        if args.output.resolve() in {
            p.resolve() for p in (args.source, args.questions, args.reviews)
        }:
            raise ValueError("Review packet output cannot overwrite dataset input files")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(review_packet(workspace), encoding="utf-8")
        print(json.dumps({"review_packet": str(args.output), "examples": len(workspace.records)}))
        return 0
    print(freeze(workspace, args.output).model_dump_json(indent=2))
    return 0
