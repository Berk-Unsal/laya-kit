"""Conservative lexical baseline. Multiple category signals mean no precise diagnosis."""

import re
from time import perf_counter

from . import __version__
from .contract import CHECKS, explanation
from .schemas import Cause, EvidenceAssessment, EvidenceStatus, Incident, Prediction

PATTERNS = {
    Cause.IMAGE_REFERENCE: (
        r"\bmanifest unknown\b",
        r"\bmanifest not found\b",
        r"\bname unknown\b",
        r"\binvalid (?:image )?reference(?: format)?\b",
        r"\binvalidimagename\b",
        r"\b(?:image|tag) [^\n]{0,100}not found\b",
        r"\bno matching manifest\b",
        r"\brepository does not exist\b",
    ),
    Cause.REGISTRY_AUTH: (
        r"\bunauthorized\b",
        r"\bdenied\b",
        r"\bauthentication required\b",
        r"\binsufficient_scope\b",
        r"\bno basic auth credentials\b",
        r"\bforbidden\b",
        r"\b(?:http(?:/\d(?:\.\d)?)?\s*|status(?: code)?[: =]*)(?:401|403)\b",
    ),
    Cause.REGISTRY_CONNECTIVITY: (
        r"\b(?:connection|connect|i/o|tls handshake) (?:timed out|timeout|refused)\b",
        r"\bcontext deadline exceeded\b",
        r"\bno such host\b",
        r"\bnetwork is unreachable\b",
        r"\bdial tcp[^\n]{0,160}\btimeout\b",
    ),
    Cause.REGISTRY_RATE_LIMIT: (
        r"\b(?:http(?:/\d(?:\.\d)?)?\s*|status(?: code)?[: =]*)429\b",
        r"\b429 too many requests\b",
        r"\btoomanyrequests\b",
        r"\b(?:pull |registry )?rate limit(?:ed| exceeded)?\b",
    ),
    Cause.OTHER: (
        r"\bx509:",
        r"\bcertificate (?:has expired|signed by unknown authority)\b",
        r"\bno space left on device\b",
        r"\bdigest mismatch\b",
        r"\bunsupported media type\b",
    ),
}
COMPILED = {cause: [re.compile(p, re.I) for p in patterns] for cause, patterns in PATTERNS.items()}


def assess_evidence(incident: Incident) -> EvidenceAssessment:
    # Do not match image names, JSON keys, or separate records joined into a synthetic sentence.
    texts = [e.message for e in incident.events] + [e.reason for e in incident.events if e.reason]
    texts += [w.reason for w in incident.waiting]
    texts += [w.message for w in incident.waiting if w.message]
    texts += incident.log_excerpts
    matches = [
        cause
        for cause, patterns in COMPILED.items()
        if any(p.search(text) for text in texts for p in patterns)
    ]
    if len(matches) > 1:
        status = EvidenceStatus.CONFLICTING
    elif matches == [Cause.OTHER]:
        status = EvidenceStatus.OTHER
    elif matches:
        status = EvidenceStatus.SPECIFIC
    else:
        status = EvidenceStatus.INCOMPLETE
    return EvidenceAssessment(status=status, matched_causes=matches)


class RulesProvider:
    model = "image-pull-rules-v1"

    def predict(self, incident: Incident) -> Prediction:
        start = perf_counter()
        assessment = assess_evidence(incident)
        selected = (
            assessment.matched_causes[0]
            if assessment.status == EvidenceStatus.SPECIFIC
            else Cause.OTHER
        )
        return Prediction(
            provider="rules",
            execution_kind="deterministic",
            model=self.model,
            runtime_version=__version__,
            selected_cause=selected,
            evidence_assessment=assessment,
            recommended_check=CHECKS[selected],
            explanation=explanation(selected, assessment),
            inference_ms=(perf_counter() - start) * 1000,
        )
