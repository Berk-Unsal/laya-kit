import pytest
from pydantic import ValidationError

from kubernetes_triage.rules import RulesProvider
from kubernetes_triage.schemas import Cause, EvidenceStatus, Fixture, Incident, PredictRequest


def test_manually_authored_regression_cases(records):
    for record in records:
        fixture = Fixture.model_validate(record)
        result = RulesProvider().predict(fixture.incident)
        assert result.selected_cause == fixture.expected_cause, fixture.id
        assert result.probabilities is None and result.ranked_options is None
        assert result.review_status == "required"


@pytest.mark.parametrize(
    "record,status",
    [
        ({"waiting": [{"reason": "ImagePullBackOff"}]}, EvidenceStatus.INCOMPLETE),
        ({"images": ["registry/unauthorized:429"]}, EvidenceStatus.INCOMPLETE),
        (
            {"events": [{"message": "x509: certificate signed by unknown authority"}]},
            EvidenceStatus.OTHER,
        ),
        (
            {"events": [{"message": "manifest unknown"}, {"message": "HTTP 401 unauthorized"}]},
            EvidenceStatus.CONFLICTING,
        ),
        ({"events": [{"message": "HTTP 429 and connection timeout"}]}, EvidenceStatus.CONFLICTING),
    ],
)
def test_other_selection_preserves_evidence_distinction(record, status):
    prediction = RulesProvider().predict(Incident.model_validate(record))
    assert prediction.selected_cause == Cause.OTHER
    assert prediction.evidence_assessment.status == status


@pytest.mark.parametrize(
    "record",
    [
        {},
        {"events": [{"message": " "}]},
        {"images": [123]},
        {"events": [{"message": "x" * 2049}]},
        {"events": [{"message": "x"}] * 33},
        {"images": ["x"] * 17},
        {"log_excerpts": ["x" * 2048] * 8, "events": [{"message": "x" * 2048}] * 8},
        {"log_excerpts": ["😺" * 2048] * 3},
        {"images": ["app:v1"], "expected_cause": "registry_auth"},
        {"waiting": [{"reason": "ErrImagePull", "remediation_command": "anything"}]},
    ],
)
def test_invalid_or_oversized_incidents_rejected(record):
    with pytest.raises(ValidationError):
        Incident.model_validate(record)


def test_provider_is_explicit_and_limited(incident):
    with pytest.raises(ValidationError):
        PredictRequest(provider="auto", incident=incident)


def test_rule_signals_do_not_cross_record_boundaries():
    incident = Incident(events=[{"message": "HTTP"}, {"message": "429"}])
    assert RulesProvider().predict(incident).evidence_assessment.status == EvidenceStatus.INCOMPLETE
