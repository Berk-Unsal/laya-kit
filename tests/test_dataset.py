"""Test-only approvals live in tmp_path; shipped dataset remains entirely pending."""

import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

import kubernetes_triage.cli as cli
import kubernetes_triage.dataset as dataset
from kubernetes_triage.contract import model_questions, model_state
from kubernetes_triage.dataset import (
    DatasetError,
    DraftRecord,
    ReviewEvent,
    append_review,
    build_splits,
    digest,
    freeze,
    load_release,
    load_workspace,
    question_hash,
    record_hash,
    review_packet,
    validation_summary,
)
from kubernetes_triage.rules import RulesProvider
from kubernetes_triage.schemas import Cause

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "datasets/v0.1"


@pytest.fixture
def paths(tmp_path):
    source, questions, reviews = (
        tmp_path / name for name in ("drafts.jsonl", "question-schema.json", "reviews.jsonl")
    )
    source.write_bytes((CORPUS / "drafts.jsonl").read_bytes())
    questions.write_bytes((CORPUS / "question-schema.json").read_bytes())
    return source, questions, reviews


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def save_rows(path, records):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


def test_event(record, snapshot, *, label=None, decision="approved"):
    return ReviewEvent(
        schema_version="1",
        dataset_version="0.1",
        event_id=uuid4().hex,
        example_id=record.example_id,
        record_hash=record_hash(record),
        question_hash=question_hash(snapshot),
        decision=decision,
        final_label=(label or record.proposed_cause) if decision == "approved" else None,
        reviewer="pytest-test-only-reviewer",
        reviewed_at=datetime.now(timezone.utc),
        notes="Temporary test-only decision, not a completed human corpus review.",
    )


# This is a helper, not a pytest test requiring record/snapshot fixtures.
test_event.__test__ = False


def approved_workspace(paths, *, variant=False):
    workspace = load_workspace(*paths)
    if variant:
        first = workspace.records[0]
        payload = first.model_dump(mode="json")
        payload["example_id"] += "-variant"
        payload["state"]["log_excerpts"] = ["Temporary test-only wording variant of this incident"]
        workspace.records.append(DraftRecord.model_validate(payload))
    workspace.reviews = [test_event(r, workspace.questions) for r in workspace.records]
    return workspace


def add_review(paths, *, label=None, decision="approved", example_id=None):
    workspace = load_workspace(*paths)
    record = workspace.records[0]
    return append_review(
        source=paths[0],
        questions=paths[1],
        reviews=paths[2],
        example_id=example_id or record.example_id,
        decision=decision,
        label=(label or record.proposed_cause) if decision == "approved" else None,
        reviewer="pytest-test-only-reviewer",
        notes="Temporary explicit test decision.",
    )


def test_shipped_corpus_is_25_distinct_pending_synthetic_families(records, tmp_path):
    workspace = load_workspace(
        CORPUS / "drafts.jsonl",
        CORPUS / "question-schema.json",
        tmp_path / "isolated-empty-review-log.jsonl",
    )
    summary = validation_summary(workspace)
    assert summary["valid"] and summary["families"] == summary["examples"] == 25
    assert summary["review_status"] == {"pending": 25, "approved": 0, "rejected": 0, "stale": 0}
    assert summary["proposed_counts"] == {cause.value: 5 for cause in Cause}
    assert not summary["release_ready"]
    regression_evidence = {
        digest(model_state(dataset.Incident.model_validate(r["incident"]))) for r in records
    }
    assert not regression_evidence.intersection(
        digest(model_state(r.state)) for r in workspace.records
    )
    for r in workspace.records:
        assert r.synthetic and r.provenance.author == "Codex"
        assert r.reference_rationale and r.evidence_status


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(proposed_cause="invented"),
        lambda r: r.update(schema_version="2"),
        lambda r: r.update(dataset_version="0.2"),
        lambda r: r.update(synthetic=False),
        lambda r: r.update(example_id=" "),
        lambda r: r.update(evidence_status="certain"),
        lambda r: r.update(provenance={"author": "", "source_note": "x", "redaction_note": "x"}),
        lambda r: r.update(state={"events": [{"message": "x" * 2049}]}),
        lambda r: r.update(state={"images": ["app:v1"], "correct_answer": "image_reference"}),
        lambda r: r.update(question_schema_version="unsupported"),
    ],
)
def test_malformed_records_rejected(paths, mutation):
    data = rows(paths[0])
    mutation(data[0])
    save_rows(paths[0], data)
    with pytest.raises(ValueError):
        load_workspace(*paths)


@pytest.mark.parametrize(
    "text", ['{"broken":', '{"schema_version":"1","schema_version":"1"}', '{"state":NaN}', "[]"]
)
def test_malformed_jsonl_rejected(paths, text):
    paths[0].write_text(text + "\n")
    with pytest.raises(ValueError):
        load_workspace(*paths)


@pytest.mark.parametrize("duplicate", ["id", "evidence"])
def test_duplicates_across_families_rejected(paths, duplicate):
    data = rows(paths[0])
    if duplicate == "id":
        data[1]["example_id"] = data[0]["example_id"]
    else:
        data[1]["state"] = data[0]["state"]
    save_rows(paths[0], data)
    with pytest.raises(DatasetError, match="Duplicate"):
        load_workspace(*paths)


def test_append_only_review_and_label_correction(paths):
    before_source = paths[0].read_bytes()
    first = add_review(paths)
    original_log = paths[2].read_bytes()
    second = add_review(paths, label=Cause.REGISTRY_AUTH)
    assert paths[2].read_bytes().startswith(original_log)
    assert paths[0].read_bytes() == before_source
    workspace = load_workspace(*paths)
    assert workspace.reviews == [first, second]
    assert workspace.latest_reviews()[first.example_id].final_label == Cause.REGISTRY_AUTH
    assert workspace.records[0].proposed_cause == Cause.IMAGE_REFERENCE
    assert workspace.status(workspace.records[0]) == "approved"


def test_source_removed_during_review_does_not_append_decision(paths, monkeypatch):
    original = dataset.load_workspace
    calls = []

    def remove_during_reload(*args):
        workspace = original(*args)
        calls.append(1)
        if len(calls) == 2:
            workspace.records.pop(0)
        return workspace

    record = original(*paths).records[0]
    monkeypatch.setattr(dataset, "load_workspace", remove_during_reload)
    with pytest.raises(DatasetError, match="Source changed"):
        append_review(
            source=paths[0],
            questions=paths[1],
            reviews=paths[2],
            example_id=record.example_id,
            decision="approved",
            label=record.proposed_cause,
            reviewer="pytest-test-only-reviewer",
            notes="Temporary test-only decision",
        )
    assert paths[2].read_text() == ""


def test_rejection_supersedes_approval(paths, tmp_path):
    add_review(paths)
    add_review(paths, decision="rejected")
    workspace = load_workspace(*paths)
    assert workspace.status(workspace.records[0]) == "rejected"
    with pytest.raises(DatasetError, match="current approval"):
        freeze(workspace, tmp_path / "release")
    assert not (tmp_path / "release").exists()


def test_approval_requires_label_identity_and_notes(paths):
    workspace = load_workspace(*paths)
    args = {
        "source": paths[0],
        "questions": paths[1],
        "reviews": paths[2],
        "example_id": workspace.records[0].example_id,
        "decision": "approved",
        "label": None,
        "reviewer": "pytest-test-only-reviewer",
        "notes": "Test decision",
    }
    for invalid in (
        {},
        {"label": Cause.IMAGE_REFERENCE, "reviewer": " "},
        {"label": Cause.IMAGE_REFERENCE, "notes": " "},
        {"decision": "rejected", "label": Cause.IMAGE_REFERENCE},
    ):
        with pytest.raises(ValidationError):
            append_review(**(args | invalid))
    assert not paths[2].exists()


@pytest.mark.parametrize("field", ["state", "reference_rationale", "proposed_cause", "provenance"])
def test_source_edits_invalidate_approval(paths, tmp_path, field):
    add_review(paths)
    original_record = load_workspace(*paths).records[0]
    data = rows(paths[0])
    if field == "state":
        data[0][field]["log_excerpts"] = ["New evidence requiring review"]
    elif field == "reference_rationale":
        data[0][field] += " Updated draft rationale."
    elif field == "proposed_cause":
        data[0][field] = Cause.OTHER.value
    else:
        data[0][field]["source_note"] += " Updated source note."
    save_rows(paths[0], data)
    workspace = load_workspace(*paths)
    assert workspace.status(workspace.records[0]) == "stale"
    assert not validation_summary(workspace)["valid"]
    with pytest.raises(DatasetError):
        freeze(workspace, tmp_path / "release")
    add_review(paths)
    assert load_workspace(*paths).status(original_record) == "stale"
    current = load_workspace(*paths)
    assert current.status(current.records[0]) == "approved"


def test_question_change_invalidates_reviews(paths, monkeypatch):
    add_review(paths)
    updated = copy.deepcopy(model_questions())
    updated["cause"]["instructions"] += " Updated authored question."
    monkeypatch.setattr(dataset, "model_questions", lambda: updated)
    payload = json.loads(paths[1].read_text())
    payload["questions"] = updated
    paths[1].write_text(json.dumps(payload))
    workspace = load_workspace(*paths)
    assert workspace.status(workspace.records[0]) == "stale"


@pytest.mark.parametrize("change", ["instructions", "criteria_order", "option_order"])
def test_question_and_order_compatibility(paths, change):
    payload = json.loads(paths[1].read_text())
    if change == "instructions":
        payload["questions"]["cause"]["instructions"] = "Different question"
    elif change == "criteria_order":
        payload["questions"]["cause"]["criteria"] = dict(
            reversed(list(payload["questions"]["cause"]["criteria"].items()))
        )
    else:
        payload["option_order"].reverse()
    paths[1].write_text(json.dumps(payload))
    with pytest.raises(ValidationError):
        load_workspace(*paths)


def test_concurrent_appends_preserve_all_events(paths):
    with ThreadPoolExecutor(max_workers=4) as executor:
        events = list(executor.map(lambda _: add_review(paths), range(8)))
    loaded = load_workspace(*paths)
    assert len(loaded.reviews) == 8
    assert {r.event_id for r in loaded.reviews} == {r.event_id for r in events}


def test_log_without_trailing_newline_can_be_appended(paths):
    add_review(paths)
    paths[2].write_bytes(paths[2].read_bytes().rstrip(b"\n"))
    add_review(paths)
    assert len(load_workspace(*paths).reviews) == 2


@pytest.mark.parametrize("bad_log", ["unknown_example", "duplicate_event"])
def test_invalid_review_log(paths, bad_log):
    add_review(paths)
    data = rows(paths[2])
    if bad_log == "unknown_example":
        data[0]["example_id"] = "unknown-example"
    else:
        data.append(data[0])
    save_rows(paths[2], data)
    with pytest.raises(DatasetError):
        load_workspace(*paths)


def test_review_packet_is_self_contained_without_source_changes(paths):
    before = [p.read_bytes() if p.exists() else None for p in paths]
    workspace = load_workspace(*paths)
    text = review_packet(workspace)
    for record in workspace.records:
        assert record.example_id in text and record.reference_rationale in text
        assert record_hash(record) in text
    assert '"pending": 25' in text and '"latest_review": null' in text
    assert "Proposed labels are not reviewed ground truth" in text
    assert [p.read_bytes() if p.exists() else None for p in paths] == before


def test_pending_corpus_cannot_freeze_or_be_loaded_as_release(paths, tmp_path):
    with pytest.raises(DatasetError, match="current approval"):
        freeze(load_workspace(*paths), tmp_path / "release")
    with pytest.raises(OSError):
        load_release(paths[0].parent)


def test_grouped_splits_are_deterministic_and_keep_variants_together(paths, tmp_path):
    workspace = approved_workspace(paths, variant=True)
    manifest = freeze(workspace, tmp_path / "release")
    release = load_release(tmp_path / "release")
    assert release.manifest == manifest
    assert len(release.records) == 26
    assert Counter(release.splits.families.values()) == {"train": 15, "calibration": 5, "test": 5}
    reversed_records = list(reversed(release.records))
    assert build_splits(reversed_records) == release.splits
    for cause in Cause:
        family_ids = {
            r.draft.incident_family_id for r in release.records if r.review.final_label == cause
        }
        assert Counter(release.splits.families[f] for f in family_ids) == {
            "train": 3,
            "calibration": 1,
            "test": 1,
        }
    first_id = workspace.records[0].example_id
    assert any(
        {first_id, first_id + "-variant"} <= set(ids) for ids in release.splits.examples.values()
    )
    all_ids = [eid for ids in release.splits.examples.values() for eid in ids]
    assert len(all_ids) == len(set(all_ids)) == 26
    assert not ((tmp_path / "release/records.jsonl").stat().st_mode & 0o222)
    with pytest.raises(DatasetError, match="existing release"):
        freeze(workspace, tmp_path / "release")


@pytest.mark.parametrize("problem", ["family_conflict", "class_balance", "family_count"])
def test_release_requires_balanced_adjudicated_families(paths, tmp_path, problem):
    workspace = approved_workspace(paths, variant=problem == "family_conflict")
    if problem == "family_count":
        workspace.records.pop()
        workspace.reviews.pop()
    else:
        index = -1 if problem == "family_conflict" else 0
        workspace.reviews[index] = test_event(
            workspace.records[index], workspace.questions, label=Cause.REGISTRY_AUTH
        )
    with pytest.raises(DatasetError):
        freeze(workspace, tmp_path / "release")
    assert not (tmp_path / "release").exists()


def rewrite_artifact(release_path, name, change, *, refresh_hash=False):
    path = release_path / name
    data = change(path.read_bytes())
    path.chmod(0o644)
    path.write_bytes(data)
    if refresh_hash:
        manifest_path = release_path / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        updated_hash = hashlib.sha256(data).hexdigest()
        manifest["files"][name] = updated_hash
        if name == "records.jsonl":
            manifest["dataset_hash"] = updated_hash
        if name == "splits.json":
            manifest["split_hash"] = updated_hash
        manifest_path.chmod(0o644)
        manifest_path.write_text(json.dumps(manifest))


@pytest.mark.parametrize("artifact", ["records.jsonl", "question-schema.json", "splits.json"])
def test_release_content_tampering_is_detected(paths, tmp_path, artifact):
    output = tmp_path / "release"
    freeze(approved_workspace(paths), output)
    rewrite_artifact(output, artifact, lambda data: data + b" ")
    with pytest.raises(DatasetError, match="content hash mismatch"):
        load_release(output)


def test_rehashed_split_tampering_still_fails_policy_validation(paths, tmp_path):
    output = tmp_path / "release"
    freeze(approved_workspace(paths), output)

    def modify(data):
        payload = json.loads(data)
        family = next(iter(payload["families"]))
        payload["families"][family] = "test" if payload["families"][family] != "test" else "train"
        return json.dumps(payload).encode()

    rewrite_artifact(output, "splits.json", modify, refresh_hash=True)
    with pytest.raises(DatasetError, match="split policy"):
        load_release(output)


def test_rehashed_record_tampering_still_requires_fresh_approval(paths, tmp_path):
    output = tmp_path / "release"
    freeze(approved_workspace(paths), output)

    def modify(data):
        payload = [json.loads(line) for line in data.decode().splitlines()]
        payload[0]["draft"]["reference_rationale"] += " Changed after approval."
        return ("\n".join(json.dumps(row) for row in payload) + "\n").encode()

    rewrite_artifact(output, "records.jsonl", modify, refresh_hash=True)
    with pytest.raises(DatasetError, match="stale approval"):
        load_release(output)


def test_release_question_drift_after_code_change_fails(paths, tmp_path, monkeypatch):
    output = tmp_path / "release"
    freeze(approved_workspace(paths), output)
    updated = copy.deepcopy(model_questions())
    updated["cause"]["instructions"] += " New runtime question."
    monkeypatch.setattr(dataset, "model_questions", lambda: updated)
    with pytest.raises(ValidationError):
        load_release(output)


def test_cli_dataset_flow_and_review_arguments(paths, tmp_path, capsys):
    common = ["--source", str(paths[0]), "--questions", str(paths[1]), "--reviews", str(paths[2])]
    assert cli.main(["dataset", "validate", *common]) == 0
    assert json.loads(capsys.readouterr().out)["review_status"]["pending"] == 25
    packet = tmp_path / "packet.md"
    assert cli.main(["dataset", "review-packet", *common, "--output", str(packet)]) == 0
    capsys.readouterr()
    record = load_workspace(*paths).records[0]
    args = [
        "dataset",
        "review",
        *common,
        "--example-id",
        record.example_id,
        "--decision",
        "approved",
        "--reviewer",
        "pytest-test-only-reviewer",
        "--note",
        "Test decision",
    ]
    assert cli.main(args) == 2  # no implicit use of proposed label
    capsys.readouterr()
    assert cli.main([*args, "--label", Cause.REGISTRY_AUTH.value]) == 0
    assert json.loads(capsys.readouterr().out)["final_label"] == Cause.REGISTRY_AUTH
    assert cli.main(["dataset", "freeze", *common, "--output", str(tmp_path / "release")]) == 2
    assert "current approval" in capsys.readouterr().err
    assert cli.main(["dataset", "review-packet", *common, "--output", str(paths[0])]) == 2
    assert "cannot overwrite" in capsys.readouterr().err


def test_dataset_evaluation_isolates_labels_and_exports_provenance(paths, tmp_path, monkeypatch):
    output = tmp_path / "release"
    freeze(approved_workspace(paths), output)
    captured = []

    class Service:
        def __init__(self, **kwargs):
            self.rules = RulesProvider()

        def predict(self, incident, provider):
            captured.append(model_state(incident))
            return self.rules.predict(incident)

    monkeypatch.setattr(cli, "TriageService", Service)
    md, data = tmp_path / "evaluation.md", tmp_path / "evaluation.json"
    assert (
        cli.main(
            [
                "evaluate",
                "--dataset",
                str(output),
                "--split",
                "test",
                "--report",
                str(md),
                "--json-report",
                str(data),
            ]
        )
        == 0
    )
    release = load_release(output)
    report = json.loads(data.read_text())
    assert report["dataset"] == release.report_provenance("test")
    assert report["summary"]["total"] == len(captured) == 5
    assert report["dataset"]["dataset_hash"] in md.read_text()
    for case, state in zip(report["cases"], captured):
        reviewed = case["dataset_record"]
        assert state == model_state(DraftRecord.model_validate(reviewed["draft"]).state)
        assert case["fixture"]["expected_cause"] == reviewed["review"]["final_label"]
        assert case["fixture"]["reference_rationale"] == reviewed["review"]["notes"]
        for key in (
            "reviewer",
            "proposed_cause",
            "reference_rationale",
            "final_label",
            "provenance",
        ):
            assert key not in json.dumps(state)


def test_frozen_evaluation_uses_corrected_gold_instead_of_proposal(paths, tmp_path):
    workspace = approved_workspace(paths)
    # Swap two test-only decisions to retain five families per final class.
    # The preserved source proposals must not override either adjudicated label.
    workspace.reviews[0] = test_event(
        workspace.records[0], workspace.questions, label=Cause.REGISTRY_AUTH
    )
    workspace.reviews[5] = test_event(
        workspace.records[5], workspace.questions, label=Cause.IMAGE_REFERENCE
    )
    output = tmp_path / "release"
    freeze(workspace, output)
    release = load_release(output)
    fixtures = {f["id"]: f for split in dataset.SPLITS for f in release.evaluation_records(split)}
    for index in (0, 5):
        draft = workspace.records[index]
        fixture = fixtures[draft.example_id]
        assert fixture["expected_cause"] == workspace.reviews[index].final_label.value
        assert fixture["expected_cause"] != draft.proposed_cause.value
        assert fixture["reference_rationale"] == workspace.reviews[index].notes
        assert fixture["reference_rationale"] != draft.reference_rationale


def test_cli_evaluation_rejects_bad_release_before_any_prediction(
    paths, tmp_path, monkeypatch, capsys
):
    class Service:
        def __init__(self, **kwargs):
            self.rules = RulesProvider()

        def predict(self, *args):
            pytest.fail("Invalid release reached inference")

    monkeypatch.setattr(cli, "TriageService", Service)
    assert (
        cli.main(
            [
                "evaluate",
                "--dataset",
                str(paths[0].parent),
                "--split",
                "test",
                "--report",
                str(tmp_path / "report.md"),
            ]
        )
        == 2
    )
    assert not (tmp_path / "report.md").exists()
    capsys.readouterr()
    assert (
        cli.main(["evaluate", "--dataset", str(tmp_path), "--report", str(tmp_path / "report.md")])
        == 2
    )
    assert "explicit --split" in capsys.readouterr().err
    assert cli.main(["evaluate", "--split", "test", "--report", str(tmp_path / "report.md")]) == 2
    capsys.readouterr()
    with pytest.raises(SystemExit) as caught:
        cli.main(
            [
                "evaluate",
                "--dataset",
                str(tmp_path),
                "--fixtures",
                str(paths[0]),
                "--report",
                str(tmp_path / "report.md"),
            ]
        )
    assert caught.value.code == 2


def test_dataset_cli_never_constructs_provider(paths, monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("Dataset commands must not create providers")

    monkeypatch.setattr(cli, "TriageService", forbidden)
    assert (
        cli.main(
            [
                "dataset",
                "validate",
                "--source",
                str(paths[0]),
                "--questions",
                str(paths[1]),
                "--reviews",
                str(paths[2]),
            ]
        )
        == 0
    )
    capsys.readouterr()


def test_dataset_commands_work_with_ml_imports_blocked():
    code = """
import sys
class BlockML:
    def find_spec(self, name, *args):
        if name.startswith(("mlx", "laya_mlx", "huggingface_hub", "torch")):
            raise AssertionError("Unexpected ML import: " + name)
sys.meta_path.insert(0, BlockML())
from kubernetes_triage.cli import main
assert main(["dataset", "validate"]) == 0
"""
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True, capture_output=True)
