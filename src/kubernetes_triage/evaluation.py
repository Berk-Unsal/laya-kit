"""Fixture evaluation with explicit valid/error/unevaluated accounting and raw evidence."""

import json
import platform
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from pydantic import ValidationError

from .contract import model_questions
from .schemas import Cause, Fixture


def evaluate(records: list, predict, *, provider: str, model: str) -> dict:
    cases = []
    seen = set()
    for index, record in enumerate(records):
        case = {
            "id": f"invalid-{index + 1}",
            "status": "unevaluated",
            "fixture": record,
            "prediction": None,
            "error": None,
        }
        try:
            fixture = Fixture.model_validate(record)
            case["id"] = fixture.id
            if fixture.id in seen:
                raise ValueError(f"Duplicate fixture id: {fixture.id}")
            seen.add(fixture.id)
        except (ValidationError, ValueError) as exc:
            case["error"] = {"code": "invalid_fixture", "message": str(exc)}
            cases.append(case)
            continue
        case["fixture"] = fixture.model_dump(mode="json")
        try:
            # Pass only the validated incident. Labels/rationales stay in the evaluator.
            prediction = predict(fixture.incident)
            case["prediction"] = prediction.model_dump(mode="json")
            case["status"] = "valid"
            case["correct"] = prediction.selected_cause == fixture.expected_cause
        except Exception as exc:
            case["status"] = "error"
            case["error"] = {
                "code": getattr(exc, "code", "prediction_error"),
                "message": str(exc),
                "inference_ms": getattr(exc, "inference_ms", None),
                "raw_response": getattr(exc, "raw_response", None),
            }
        cases.append(case)
    valid = [c for c in cases if c["status"] == "valid"]
    correct = sum(c["correct"] for c in valid)
    attempted = sum(c["status"] != "unevaluated" for c in cases)
    per_class = {}
    for cause in Cause:
        eligible = [c for c in valid if c["fixture"]["expected_cause"] == cause.value]
        per_class[cause.value] = {
            "valid": len(eligible),
            "correct": sum(c["correct"] for c in eligible),
        }
    high_prob_mistakes = [
        c["id"]
        for c in valid
        if not c["correct"]
        and c["prediction"]["probabilities"] is not None
        and max(c["prediction"]["probabilities"].values()) >= 0.8
    ]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "environment": {
            "python": platform.python_version(),
            "os": platform.platform(),
            "machine": platform.machine(),
        },
        "question_schema": model_questions() if provider == "laya" else None,
        "cases": cases,
        "summary": {
            "total": len(cases),
            "attempted": attempted,
            "valid": len(valid),
            "correct": correct,
            "errors": sum(c["status"] == "error" for c in cases),
            "unevaluated": len(cases) - attempted,
            "accuracy_valid": correct / len(valid) if valid else None,
            "correct_fraction_attempted": correct / attempted if attempted else None,
            "median_inference_ms_valid": median(c["prediction"]["inference_ms"] for c in valid)
            if valid
            else None,
            "execution_kinds": dict(Counter(c["prediction"]["execution_kind"] for c in valid)),
            "high_probability_mistakes_at_0_8": high_prob_mistakes,
            "per_class": per_class,
        },
    }


def json_block(value) -> str:
    content = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
    # Evidence may contain Markdown fences. A longer fence keeps it inert and the report intact.
    fence = "`" * max(3, max((len(m.group()) for m in re.finditer(r"`+", content)), default=0) + 1)
    return f"{fence}json\n{content}\n{fence}"


def markdown_report(report: dict) -> str:
    lines = [
        "# Kubernetes image-pull fixture evaluation",
        "",
        "Manually authored synthetic regression fixtures; not a production accuracy estimate "
        "or a sufficient training dataset. All predictions require human review.",
        "",
        "Latency covers rules classification or Laya evidence preparation plus synchronized predict, "
        "excluding output validation, checkpoint loading, and lock wait. First-load time is recorded "
        "separately. No probabilities are invented for rules.",
        "",
        "Injected test-agent outputs, if present, are simulations and are not real model "
        "measurements. Errors and unevaluated fixtures are not valid predictions.",
        "",
        "## Run and scoring",
        "",
        json_block({k: v for k, v in report.items() if k != "cases"}),
        "",
    ]
    for index, case in enumerate(report["cases"], 1):
        lines += [
            f"## Case {index}",
            "",
            json_block(
                {
                    "id": case["id"],
                    "status": case["status"],
                    "correct": case.get("correct"),
                    "fixture": case["fixture"],
                    "error": case["error"],
                }
            ),
            "",
            "### Prediction (including full raw response)",
            "",
            json_block(case["prediction"]),
            "",
        ]
    return "\n".join(lines)


def write_reports(report: dict, markdown_path: Path, json_path: Path | None = None):
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
