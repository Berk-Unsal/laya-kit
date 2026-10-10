"""Offline, explicitly reviewed datasets. No provider is used to author or approve labels."""

import hashlib
import json
import os
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal, Self
from uuid import uuid4

from pydantic import AwareDatetime, Field, StringConstraints, model_validator

from .contract import model_questions, model_state
from .evaluation import json_block
from .schemas import Cause, EvidenceStatus, Incident, Message, ShortText, StrictModel

DEFAULT_SOURCE = Path("datasets/v0.1/drafts.jsonl")
DEFAULT_QUESTIONS = Path("datasets/v0.1/question-schema.json")
DEFAULT_REVIEWS = Path("datasets/v0.1/reviews.jsonl")
QUESTION_VERSION = "image-pull-cause-v1"
SPLITS = ("train", "calibration", "test")
MAX_FILE_BYTES = 8_000_000
Identifier = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-z0-9][a-z0-9_.-]{0,79}$")]
Digest = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-f0-9]{64}$")]


class DatasetError(ValueError):
    pass


class QuestionSnapshot(StrictModel):
    schema_version: Literal["1"]
    question_schema_version: Literal["image-pull-cause-v1"]
    questions: dict
    option_order: list[Cause] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def compatible(self) -> Self:
        expected = model_questions()
        if self.questions != expected:
            raise ValueError("Question snapshot differs from the current authored question")
        order = list(expected["cause"]["criteria"])
        if list(self.questions["cause"]["criteria"]) != order or self.option_order != order:
            raise ValueError("Question option order differs from the current contract")
        return self


class Provenance(StrictModel):
    author: ShortText
    source_note: Message
    redaction_note: Message


class DraftRecord(StrictModel):
    schema_version: Literal["1"]
    dataset_version: Literal["0.1"]
    example_id: Identifier
    incident_family_id: Identifier
    synthetic: Literal[True]
    provenance: Provenance
    question_schema_version: Literal["image-pull-cause-v1"]
    state: Incident
    proposed_cause: Cause
    reference_rationale: Message
    evidence_status: EvidenceStatus


class ReviewEvent(StrictModel):
    schema_version: Literal["1"]
    dataset_version: Literal["0.1"]
    event_id: Identifier
    example_id: Identifier
    record_hash: Digest
    question_hash: Digest
    decision: Literal["approved", "rejected"]
    final_label: Cause | None
    reviewer: ShortText
    reviewed_at: AwareDatetime
    notes: Message

    @model_validator(mode="after")
    def require_explicit_decision(self) -> Self:
        if self.decision == "approved" and self.final_label is None:
            raise ValueError("Approval requires an explicit final label")
        if self.decision == "rejected" and self.final_label is not None:
            raise ValueError("Rejection cannot supply a final label")
        return self


class ReviewedRecord(StrictModel):
    draft: DraftRecord
    review: ReviewEvent


class SplitManifest(StrictModel):
    schema_version: Literal["1"]
    seed: Literal[42]
    families: dict[Identifier, Literal["train", "calibration", "test"]]
    examples: dict[str, list[Identifier]]


class ReleaseManifest(StrictModel):
    schema_version: Literal["1"]
    dataset_version: Literal["0.1"]
    created_at: AwareDatetime
    question_hash: Digest
    dataset_hash: Digest
    split_hash: Digest
    files: dict[str, Digest]


def digest(value: object) -> str:
    canonical = json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def record_hash(record: DraftRecord) -> str:
    return digest(record.model_dump(mode="json"))


def question_hash(snapshot: QuestionSnapshot) -> str:
    # option_order is an explicit list, so canonical key sorting cannot erase ordering semantics.
    return digest(snapshot.model_dump(mode="json"))


def _parse_json(text: str):
    def reject_constant(value):
        raise DatasetError(f"Non-finite JSON constant: {value}")

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DatasetError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(text, parse_constant=reject_constant, object_pairs_hook=unique_keys)


def _read_bytes(path: Path) -> bytes:
    with path.open("rb") as handle:
        data = handle.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise DatasetError(f"{path}: file exceeds {MAX_FILE_BYTES} bytes")
    return data


def _jsonl(text: str, model, *, description: str) -> list:
    records = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > 64_000:
            raise DatasetError(f"{description}:{line_number}: record exceeds 64000 bytes")
        try:
            records.append(model.model_validate(_parse_json(line)))
        except ValueError as exc:
            raise DatasetError(f"{description}:{line_number}: {exc}") from exc
        if len(records) > 1000:
            raise DatasetError(f"{description}: exceeds 1000 records")
    return records


def _check_sources(records: list[DraftRecord]):
    if not records:
        raise DatasetError("Dataset contains no draft records")
    ids = set()
    evidence_families = {}
    for record in records:
        if record.example_id in ids:
            raise DatasetError(f"Duplicate example ID: {record.example_id}")
        ids.add(record.example_id)
        state_hash = digest(model_state(record.state))
        previous = evidence_families.setdefault(state_hash, record.incident_family_id)
        if previous != record.incident_family_id:
            raise DatasetError(
                f"Duplicate evidence across families: {previous}, {record.incident_family_id}"
            )


def _check_review_log(reviews: list[ReviewEvent], records: list[DraftRecord]):
    ids = {record.example_id for record in records}
    events = set()
    for review in reviews:
        if review.example_id not in ids:
            raise DatasetError(f"Review references unknown example: {review.example_id}")
        if review.event_id in events:
            raise DatasetError(f"Duplicate review event: {review.event_id}")
        events.add(review.event_id)


@dataclass
class DatasetWorkspace:
    records: list[DraftRecord]
    questions: QuestionSnapshot
    reviews: list[ReviewEvent]

    def latest_reviews(self) -> dict[str, ReviewEvent]:
        # Append order is authoritative; timestamps never reorder decisions.
        return {review.example_id: review for review in self.reviews}

    def status(self, record: DraftRecord) -> str:
        latest = self.latest_reviews().get(record.example_id)
        if latest is None:
            return "pending"
        if latest.record_hash != record_hash(record) or latest.question_hash != question_hash(
            self.questions
        ):
            return "stale"
        return latest.decision


def load_workspace(
    source=DEFAULT_SOURCE, questions=DEFAULT_QUESTIONS, reviews=DEFAULT_REVIEWS
) -> DatasetWorkspace:
    source, questions, reviews = Path(source), Path(questions), Path(reviews)
    records = _jsonl(_read_bytes(source).decode("utf-8"), DraftRecord, description=str(source))
    snapshot = QuestionSnapshot.model_validate(_parse_json(_read_bytes(questions).decode("utf-8")))
    events = (
        _jsonl(_read_bytes(reviews).decode("utf-8"), ReviewEvent, description=str(reviews))
        if reviews.exists()
        else []
    )
    _check_sources(records)
    _check_review_log(events, records)
    return DatasetWorkspace(records, snapshot, events)


def validation_summary(workspace: DatasetWorkspace) -> dict:
    statuses = Counter(workspace.status(record) for record in workspace.records)
    latest = workspace.latest_reviews()
    issues = [
        f"Stale review: {r.example_id}" for r in workspace.records if workspace.status(r) == "stale"
    ]
    family_labels = defaultdict(set)
    for record in workspace.records:
        if workspace.status(record) == "approved":
            family_labels[record.incident_family_id].add(latest[record.example_id].final_label)
    issues += [
        f"Conflicting approved labels within family: {family}"
        for family, labels in family_labels.items()
        if len(labels) > 1
    ]
    family_counts = Counter(
        next(iter(labels)).value for labels in family_labels.values() if len(labels) == 1
    )
    family_total = len({r.incident_family_id for r in workspace.records})
    blockers = list(issues)
    if statuses["approved"] != len(workspace.records):
        blockers.append("Every example requires a current explicit approval")
    if family_total != 25:
        blockers.append("Pilot release requires 25 incident families")
    if any(family_counts[cause.value] != 5 for cause in Cause):
        blockers.append("Pilot release requires five approved families per final category")
    return {
        "valid": not issues,
        "dataset_version": "0.1",
        "examples": len(workspace.records),
        "families": family_total,
        "review_status": {
            status: statuses[status] for status in ("pending", "approved", "rejected", "stale")
        },
        "proposed_counts": dict(Counter(r.proposed_cause.value for r in workspace.records)),
        "approved_family_counts": {cause.value: family_counts[cause.value] for cause in Cause},
        "release_ready": not blockers,
        "release_blockers": blockers,
        "question_hash": question_hash(workspace.questions),
        "issues": issues,
    }


def review_packet(workspace: DatasetWorkspace) -> str:
    latest = workspace.latest_reviews()
    lines = [
        "# Dataset v0.1 — human review packet",
        "",
        "Synthetic drafts authored for workflow development. Proposed labels are not reviewed "
        "ground truth. No provider was run to author or approve these records.",
        "",
        "Read the evidence and rationale, then explicitly approve, correct, or reject each "
        "example using the dataset review CLI. Model review-required policy is independent.",
        "",
        "## Dataset status and typed question",
        "",
        json_block(validation_summary(workspace)),
        "",
        json_block(workspace.questions.model_dump(mode="json")),
        "",
    ]
    for index, record in enumerate(workspace.records, 1):
        review = latest.get(record.example_id)
        lines += [
            f"## {index}. {record.example_id}",
            "",
            json_block(
                {
                    "review_status": workspace.status(record),
                    "record_hash": record_hash(record),
                    "draft": record.model_dump(mode="json"),
                    "latest_review": review.model_dump(mode="json") if review else None,
                }
            ),
            "",
        ]
    return "\n".join(lines)


def append_review(
    *,
    source: Path,
    questions: Path,
    reviews: Path,
    example_id: str,
    decision: str,
    label: Cause | None,
    reviewer: str,
    notes: str,
) -> ReviewEvent:
    # POSIX advisory locking serializes read/validate/append on this local Mac/Linux workflow.
    # Import lazily so read-only dataset commands also remain usable on other platforms.
    try:
        import fcntl
    except ImportError as exc:
        raise DatasetError(
            "Appending reviews currently requires POSIX file locking (Mac/Linux)."
        ) from exc
    workspace = load_workspace(source, questions, reviews)
    record = next((r for r in workspace.records if r.example_id == example_id), None)
    if record is None:
        raise DatasetError(f"Unknown example ID: {example_id}")
    event = ReviewEvent(
        schema_version="1",
        dataset_version="0.1",
        event_id=uuid4().hex,
        example_id=example_id,
        record_hash=record_hash(record),
        question_hash=question_hash(workspace.questions),
        decision=decision,
        final_label=label,
        reviewer=reviewer,
        reviewed_at=datetime.now(timezone.utc),
        notes=notes,
    )
    reviews.parent.mkdir(parents=True, exist_ok=True)
    with reviews.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.seek(0)
            existing = handle.read(MAX_FILE_BYTES + 1)
            if len(existing.encode("utf-8")) > MAX_FILE_BYTES:
                raise DatasetError("Review log exceeds its byte limit")
            events = _jsonl(existing, ReviewEvent, description=str(reviews))
            _check_review_log(events, workspace.records)
            if len(events) >= 1000:
                raise DatasetError(
                    "Review log exceeds 1000 events; archive into a new dataset version"
                )
            # Re-read source and question under the lock; do not approve an edit made during loading.
            current = load_workspace(source, questions, reviews)
            current_record = next((r for r in current.records if r.example_id == example_id), None)
            if (
                current_record is None
                or record_hash(current_record) != event.record_hash
                or question_hash(current.questions) != event.question_hash
            ):
                raise DatasetError(
                    "Source changed while reviewing; read the updated packet and retry"
                )
            handle.seek(0, 2)
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(event.model_dump_json() + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return event


def _verify_approved(record: ReviewedRecord, snapshot: QuestionSnapshot):
    review = record.review
    if (
        review.example_id != record.draft.example_id
        or review.decision != "approved"
        or review.record_hash != record_hash(record.draft)
        or review.question_hash != question_hash(snapshot)
    ):
        raise DatasetError(f"Missing, rejected, or stale approval: {record.draft.example_id}")


def build_splits(records: list[ReviewedRecord]) -> SplitManifest:
    families = defaultdict(set)
    for record in records:
        families[record.draft.incident_family_id].add(record.review.final_label)
    if len(families) != 25:
        raise DatasetError(f"Pilot release requires 25 families; found {len(families)}")
    if any(len(labels) != 1 for labels in families.values()):
        raise DatasetError("Conflicting approved labels within a family require adjudication")
    by_class = {
        cause: sorted(family for family, labels in families.items() if labels == {cause})
        for cause in Cause
    }
    if any(len(group) != 5 for group in by_class.values()):
        raise DatasetError(
            "Pilot release requires five families per final category; "
            "revise class coverage and re-review rather than changing grouping"
        )
    rng = random.Random(42)
    assigned = {}
    for group in by_class.values():
        rng.shuffle(group)
        for family, split in zip(group, ("train", "train", "train", "calibration", "test")):
            assigned[family] = split
    examples = {
        split: sorted(
            r.draft.example_id for r in records if assigned[r.draft.incident_family_id] == split
        )
        for split in SPLITS
    }
    return SplitManifest(schema_version="1", seed=42, families=assigned, examples=examples)


def _pretty(model: StrictModel) -> bytes:
    return (model.model_dump_json(indent=2) + "\n").encode("utf-8")


def freeze(workspace: DatasetWorkspace, output: Path) -> ReleaseManifest:
    output = Path(output)
    _check_sources(workspace.records)
    _check_review_log(workspace.reviews, workspace.records)
    QuestionSnapshot.model_validate(workspace.questions.model_dump(mode="json"))
    if output.exists() or output.is_symlink():
        raise DatasetError(f"Refusing existing release output: {output}")
    summary = validation_summary(workspace)
    if summary["issues"] or any(workspace.status(r) != "approved" for r in workspace.records):
        raise DatasetError(
            "Freeze requires current approval for every record; "
            f"statuses: {summary['review_status']}; issues: {summary['issues']}"
        )
    latest = workspace.latest_reviews()
    records = [
        ReviewedRecord(draft=r, review=latest[r.example_id])
        for r in sorted(workspace.records, key=lambda r: r.example_id)
    ]
    for record in records:
        _verify_approved(record, workspace.questions)
    splits = build_splits(records)
    contents = {
        "records.jsonl": ("".join(r.model_dump_json() + "\n" for r in records)).encode("utf-8"),
        "question-schema.json": _pretty(workspace.questions),
        "splits.json": _pretty(splits),
    }
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}
    manifest = ReleaseManifest(
        schema_version="1",
        dataset_version="0.1",
        created_at=datetime.now(timezone.utc),
        question_hash=question_hash(workspace.questions),
        dataset_hash=hashes["records.jsonl"],
        split_hash=hashes["splits.json"],
        files=hashes,
    )
    # Exclusive mkdir makes the no-overwrite rule safe even for simultaneous freezes.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    try:
        for name, data in contents.items():
            with (output / name).open("xb") as handle:
                handle.write(data)
        # Commit marker last: incomplete directories are never accepted as releases.
        with (output / "manifest.json").open("xb") as handle:
            handle.write(_pretty(manifest))
        for name in (*contents, "manifest.json"):
            (output / name).chmod(0o444)
        output.chmod(0o555)
    except Exception:
        output.chmod(0o755)
        for name in (*contents, "manifest.json"):
            path = output / name
            if path.exists():
                path.unlink()
        output.rmdir()
        raise
    return manifest


@dataclass
class FrozenDataset:
    records: list[ReviewedRecord]
    questions: QuestionSnapshot
    splits: SplitManifest
    manifest: ReleaseManifest

    def evaluation_records(self, split: str) -> list[dict]:
        if split not in SPLITS:
            raise DatasetError(f"Unknown split: {split}")
        selected = set(self.splits.examples[split])
        return [
            {
                "id": r.draft.example_id,
                "group_id": r.draft.incident_family_id,
                "synthetic": r.draft.synthetic,
                "incident": model_state(r.draft.state),
                "expected_cause": r.review.final_label.value,
                "reference_rationale": r.review.notes,
            }
            for r in self.records
            if r.draft.example_id in selected
        ]

    def report_provenance(self, split: str) -> dict:
        return {
            "dataset_version": self.manifest.dataset_version,
            "split": split,
            "dataset_hash": self.manifest.dataset_hash,
            "split_hash": self.manifest.split_hash,
            "question_hash": self.manifest.question_hash,
            "synthetic": True,
            "split_seed": self.splits.seed,
        }


def load_release(directory: Path) -> FrozenDataset:
    directory = Path(directory)
    names = ("manifest.json", "records.jsonl", "question-schema.json", "splits.json")
    if any((directory / name).is_symlink() for name in names):
        raise DatasetError("Release artifacts must be regular files, not symlinks")
    manifest = ReleaseManifest.model_validate(
        _parse_json(_read_bytes(directory / "manifest.json").decode("utf-8"))
    )
    if set(manifest.files) != set(names[1:]):
        raise DatasetError("Release manifest must hash exactly records, questions, and splits")
    contents = {name: _read_bytes(directory / name) for name in names[1:]}
    for name, data in contents.items():
        if hashlib.sha256(data).hexdigest() != manifest.files[name]:
            raise DatasetError(f"Release content hash mismatch: {name}")
    if (
        manifest.dataset_hash != manifest.files["records.jsonl"]
        or manifest.split_hash != manifest.files["splits.json"]
    ):
        raise DatasetError("Dataset/split hashes disagree with the manifest file hashes")
    snapshot = QuestionSnapshot.model_validate(
        _parse_json(contents["question-schema.json"].decode("utf-8"))
    )
    if question_hash(snapshot) != manifest.question_hash:
        raise DatasetError("Question snapshot hash mismatch")
    records = _jsonl(
        contents["records.jsonl"].decode("utf-8"), ReviewedRecord, description="frozen records"
    )
    _check_sources([r.draft for r in records])
    _check_review_log([r.review for r in records], [r.draft for r in records])
    for record in records:
        _verify_approved(record, snapshot)
    splits = SplitManifest.model_validate(_parse_json(contents["splits.json"].decode("utf-8")))
    if splits != build_splits(records):
        raise DatasetError("Split manifest violates the deterministic grouped split policy")
    return FrozenDataset(records, snapshot, splits, manifest)
