import json
from pathlib import Path

import pytest

from kubernetes_triage.schemas import Cause, Incident

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def incident():
    return Incident.model_validate(
        json.loads((ROOT / "examples/manifest_unknown.json").read_text())
    )


@pytest.fixture
def records():
    return json.loads((ROOT / "fixtures/image_pull.synthetic.json").read_text())


@pytest.fixture
def raw_response():
    return {
        "model": "laya-rl-agent",
        "answers": {
            "cause": {
                "type": "choice",
                "choice": Cause.IMAGE_REFERENCE.value,
                "probabilities": {
                    c.value: 0.8 if c == Cause.IMAGE_REFERENCE else 0.05 for c in Cause
                },
                "confidence": 0.52,
                "answer_confidence": 0.8,
                "action": {"act_probability": 0.9},
            }
        },
        "usage": {
            "input_tokens": 128,
            "output_tokens": 0,
            "state_tokens": 60,
            "state_tokens_dropped": 4,
            "truncated": True,
            "truncated_questions": ["cause"],
        },
        "extra_metadata": {"preserve_me": [1, 2, 3]},
    }
