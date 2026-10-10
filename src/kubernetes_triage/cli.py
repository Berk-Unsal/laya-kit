"""Minimal CLI for explicit predictions, fixture evaluation, and loopback serving."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .dataset import SPLITS, load_release
from .dataset_cli import add_dataset_commands, run_dataset_command
from .evaluation import evaluate, write_reports
from .inference import DEFAULT_MODEL, DEFAULT_REVISION, ProviderError
from .schemas import Incident
from .service import TriageService


def read_json(path: str, max_bytes: int):
    if path == "-":
        data = sys.stdin.buffer.read(max_bytes + 1)
    else:
        with Path(path).open("rb") as handle:
            data = handle.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"Input exceeds {max_bytes} bytes")

    def reject_constant(value):
        raise ValueError(f"Non-finite JSON constant is not allowed: {value}")

    return json.loads(data, parse_constant=reject_constant)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline image-pull triage; human review required")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("predict", "evaluate", "serve"):
        command = commands.add_parser(name)
        command.add_argument("--model", default=DEFAULT_MODEL)
        command.add_argument(
            "--revision",
            default=DEFAULT_REVISION,
            help="Pinned Hub revision; use --revision for another checkpoint",
        )
        command.add_argument(
            "--allow-download",
            action="store_true",
            help="Explicitly permit public checkpoint fetching on Laya prediction",
        )
        if name != "serve":
            command.add_argument("--provider", choices=["rules", "laya"], default="rules")
        if name == "predict":
            command.add_argument(
                "--input", required=True, help="Incident JSON path, or - for stdin"
            )
        if name == "evaluate":
            inputs = command.add_mutually_exclusive_group()
            inputs.add_argument("--fixtures")
            inputs.add_argument("--dataset", type=Path, help="Verified frozen release directory")
            command.add_argument("--split", choices=SPLITS)
            command.add_argument("--report", required=True, type=Path)
            command.add_argument("--json-report", type=Path)
        if name == "serve":
            command.add_argument("--host", default="127.0.0.1")
            command.add_argument("--port", default=8000, type=int)
    add_dataset_commands(commands)
    args = parser.parse_args(argv)
    try:
        if args.command == "dataset":
            return run_dataset_command(args)
        service = TriageService(
            allow_download=args.allow_download, model=args.model, revision=args.revision
        )
        if args.command == "predict":
            incident = Incident.model_validate(read_json(args.input, 64_000))
            print(service.predict(incident, args.provider).model_dump_json(indent=2))
            return 0
        if args.command == "evaluate":
            release = None
            if args.dataset:
                if args.split is None:
                    raise ValueError("Dataset evaluation requires an explicit --split")
                release = load_release(args.dataset)
                records = release.evaluation_records(args.split)
            else:
                if args.split is not None:
                    raise ValueError("--split is only supported with --dataset")
                records = read_json(
                    args.fixtures or "fixtures/image_pull.synthetic.json", 2_000_000
                )
            if not isinstance(records, list) or not 1 <= len(records) <= 1000:
                raise ValueError("Fixtures must be a JSON list containing 1 to 1000 records")
            report = evaluate(
                records,
                lambda incident: service.predict(incident, args.provider),
                provider=args.provider,
                model=service.rules.model if args.provider == "rules" else args.model,
            )
            if release:
                report["dataset"] = release.report_provenance(args.split)
                reviewed = {r.draft.example_id: r for r in release.records}
                for case in report["cases"]:
                    case["dataset_record"] = reviewed[case["id"]].model_dump(mode="json")
            write_reports(report, args.report, args.json_report)
            print(json.dumps(report["summary"], indent=2))
            return 2 if report["summary"]["errors"] or report["summary"]["unevaluated"] else 0
        import uvicorn

        from .api import create_app

        uvicorn.run(create_app(service), host=args.host, port=args.port)
        return 0
    except (OSError, ValueError, ValidationError, ProviderError) as exc:
        print(
            json.dumps(
                {
                    "error": getattr(exc, "code", "invalid_input"),
                    "message": str(exc),
                    "raw_response": getattr(exc, "raw_response", None),
                }
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
