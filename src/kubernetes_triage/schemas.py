"""Bounded evidence and a provider-independent diagnostic contract."""

import math
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StringConstraints, model_validator


class Cause(StrEnum):
    IMAGE_REFERENCE = "image_reference"
    REGISTRY_AUTH = "registry_auth"
    REGISTRY_CONNECTIVITY = "registry_connectivity"
    REGISTRY_RATE_LIMIT = "registry_rate_limit"
    OTHER = "other_or_insufficient_evidence"


class EvidenceStatus(StrEnum):
    SPECIFIC = "specific_signal"
    OTHER = "other_signal"
    INCOMPLETE = "insufficient_evidence"
    CONFLICTING = "conflicting_signals"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


ShortText = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=256)]
Message = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=2048)]
Image = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=512)]


class Event(StrictModel):
    reason: ShortText | None = None
    message: Message


class Waiting(StrictModel):
    reason: ShortText
    message: Message | None = None
    image: Image | None = None


class Incident(StrictModel):
    events: list[Event] = Field(default_factory=list, max_length=32)
    waiting: list[Waiting] = Field(default_factory=list, max_length=16)
    images: list[Image] = Field(default_factory=list, max_length=16)
    log_excerpts: list[Message] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def bound_evidence(self) -> Self:
        if not any((self.events, self.waiting, self.images, self.log_excerpts)):
            raise ValueError("Supply at least one event, waiting state, image, or log excerpt")
        if len(self.model_dump_json().encode("utf-8")) > 24_000:
            raise ValueError("Combined incident evidence exceeds 24000 UTF-8 bytes")
        return self


class PredictRequest(StrictModel):
    provider: Literal["rules", "laya"] = "rules"
    incident: Incident


class DiagnosticCheck(StrictModel):
    id: str
    title: str
    description: str


class EvidenceAssessment(StrictModel):
    status: EvidenceStatus
    matched_causes: list[Cause]


class RankedOption(StrictModel):
    cause: Cause
    probability: float = Field(ge=0, le=1, allow_inf_nan=False)


class Prediction(StrictModel):
    provider: Literal["rules", "laya"]
    execution_kind: Literal["deterministic", "native_mlx", "injected_test"]
    model: str
    model_revision: str | None = None
    runtime_version: str
    dtype: str | None = None
    selected_cause: Cause
    probabilities: dict[Cause, float] | None = None
    ranked_options: list[RankedOption] | None = None
    evidence_assessment: EvidenceAssessment
    recommended_check: DiagnosticCheck
    inference_ms: float = Field(ge=0, allow_inf_nan=False)
    model_load_ms: float = Field(default=0, ge=0, allow_inf_nan=False)
    review_status: Literal["required"] = "required"
    review_reason: str = "Human review is required; model probabilities do not verify correctness."
    explanation_kind: Literal["authored_template"] = "authored_template"
    explanation: str
    usage: dict[str, JsonValue] | None = None
    raw_response: JsonValue = None

    @model_validator(mode="after")
    def validate_distribution(self) -> Self:
        if self.probabilities is None:
            if self.ranked_options is not None:
                raise ValueError("Ranking requires probabilities")
            return self
        if set(self.probabilities) != set(Cause):
            raise ValueError("Probabilities must include exactly the five supplied causes")
        values = list(self.probabilities.values())
        if any(not math.isfinite(p) or not 0 <= p <= 1 for p in values):
            raise ValueError("Probabilities must be finite and between zero and one")
        # Upstream rounds each of five options to four decimals; do not renormalize.
        if not math.isclose(sum(values), 1.0, abs_tol=0.0003):
            raise ValueError("Probabilities must sum to one within rounding tolerance")
        if self.probabilities[self.selected_cause] < max(values):
            raise ValueError("Selected cause is inconsistent with the probability maximum")
        expected = sorted(self.probabilities, key=lambda c: -self.probabilities[c])
        if self.ranked_options is None or [r.cause for r in self.ranked_options] != expected:
            raise ValueError("Ranked options must contain all causes in probability order")
        if any(r.probability != self.probabilities[r.cause] for r in self.ranked_options):
            raise ValueError("Ranked probabilities disagree with the distribution")
        return self


class Fixture(StrictModel):
    id: ShortText
    group_id: ShortText
    synthetic: Literal[True]
    incident: Incident
    expected_cause: Cause
    reference_rationale: Message
