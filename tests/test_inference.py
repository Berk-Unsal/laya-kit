import copy
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

import kubernetes_triage.inference as inference
from kubernetes_triage.contract import model_questions, model_state
from kubernetes_triage.inference import LayaProvider, ProviderError, parse_response
from kubernetes_triage.schemas import Cause, Fixture


def parse(raw, incident):
    return parse_response(
        raw,
        incident,
        model="explicit-test-model",
        revision="test-revision",
        runtime_version="injected-test-agent",
        inference_ms=1.0,
        injected=True,
    )


def test_full_response_ranking_and_metadata_preserved(raw_response, incident):
    result = parse(raw_response, incident)
    assert result.raw_response == raw_response
    assert result.usage == raw_response["usage"]
    assert result.ranked_options[0].cause == Cause.IMAGE_REFERENCE
    assert len(result.ranked_options) == 5
    assert result.execution_kind == "injected_test"
    assert result.model == "explicit-test-model"
    assert result.review_status == "required"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["answers"]["cause"].update(choice="invented"),
        lambda r: r["answers"]["cause"].update(type="score"),
        lambda r: r["answers"]["cause"]["probabilities"].pop("registry_auth"),
        lambda r: r["answers"]["cause"]["probabilities"].update(extra=0),
        lambda r: r["answers"]["cause"]["probabilities"].update(image_reference=-1),
        lambda r: r["answers"]["cause"]["probabilities"].update(image_reference=float("nan")),
        lambda r: r["answers"]["cause"]["probabilities"].update(image_reference=float("inf")),
        lambda r: r["answers"]["cause"]["probabilities"].update(image_reference="0.8"),
        lambda r: r["answers"]["cause"]["probabilities"].update(image_reference=True),
        lambda r: r["answers"]["cause"]["probabilities"].update(image_reference=0.2),
        lambda r: r["answers"]["cause"].update(choice="registry_auth"),
        lambda r: r["answers"].update(unrequested={}),
        lambda r: r.pop("usage"),
    ],
)
def test_invalid_model_outputs_are_errors_with_raw_evidence(raw_response, incident, mutation):
    mutation(raw_response)
    with pytest.raises(ProviderError) as caught:
        parse(raw_response, incident)
    assert caught.value.code == "invalid_response"
    assert caught.value.raw_response is not None
    json.dumps(caught.value.raw_response, allow_nan=False)


@pytest.mark.parametrize("raw", [None, [], "not a decision", {"answers": None}])
def test_malformed_response(raw, incident):
    with pytest.raises(ProviderError):
        parse(raw, incident)


def test_rounded_probabilities_are_retained(raw_response, incident):
    probs = {c.value: 0.1667 for c in Cause}
    probs[Cause.IMAGE_REFERENCE.value] = 0.3333
    raw_response["answers"]["cause"]["probabilities"] = probs
    result = parse(raw_response, incident)
    assert result.probabilities[Cause.IMAGE_REFERENCE] == 0.3333
    assert sum(result.probabilities.values()) != 1.0


def test_selected_answer_must_maximize_even_at_rounding_step(raw_response, incident):
    raw_response["answers"]["cause"]["probabilities"] = {c.value: 0.2 for c in Cause}
    raw_response["answers"]["cause"]["probabilities"][Cause.REGISTRY_AUTH.value] = 0.2001
    with pytest.raises(ProviderError, match="probability maximum"):
        parse(raw_response, incident)


def test_local_checkpoint_does_not_claim_default_hub_revision(tmp_path):
    assert LayaProvider(model=str(tmp_path)).revision is None


def test_load_once_and_isolate_labels(records, raw_response):
    calls = []
    loads = []

    class Agent:
        def predict(self, state, questions):
            calls.append((state, questions))
            return copy.deepcopy(raw_response)

    def factory():
        loads.append(1)
        return Agent()

    provider = LayaProvider(agent_factory=factory)
    fixture = Fixture.model_validate(records[0])
    assert not provider.loaded
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(provider.predict, [fixture.incident] * 8))
    assert loads == [1]
    assert provider.loaded
    assert sum(r.model_load_ms > 0 for r in results) == 1
    assert calls[0] == (model_state(fixture.incident), model_questions())
    state_text = json.dumps(calls[0][0])
    for excluded in ("expected_cause", "reference_rationale", "group_id", "synthetic"):
        assert excluded not in state_text
    assert fixture.reference_rationale not in state_text


def test_inference_failure_does_not_fallback(incident):
    def fail(*args):
        raise RuntimeError("explicit test failure")

    provider = LayaProvider(agent_factory=lambda: SimpleNamespace(predict=fail))
    with pytest.raises(ProviderError, match="explicit test failure") as caught:
        provider.predict(incident)
    assert caught.value.code == "inference_failed"


def test_unsupported_hardware_without_import_or_download(monkeypatch, incident):
    monkeypatch.setattr(inference.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        inference.importlib, "import_module", lambda name: pytest.fail(f"Unexpected import: {name}")
    )
    with pytest.raises(ProviderError) as caught:
        LayaProvider().predict(incident)
    assert caught.value.code == "unsupported_hardware"


def test_missing_optional_dependency_is_clear(monkeypatch, incident):
    monkeypatch.setattr(inference.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(inference.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(inference.platform, "mac_ver", lambda: ("14.0", (), ""))

    def missing(name):
        raise ImportError(name)

    monkeypatch.setattr(inference.importlib, "import_module", missing)
    with pytest.raises(ProviderError) as caught:
        LayaProvider().predict(incident)
    assert caught.value.code == "missing_dependency"


@pytest.mark.parametrize("allow_download", [False, True])
def test_hub_resolution_is_explicit_and_loading_uses_local_path(
    monkeypatch, tmp_path, incident, raw_response, allow_download
):
    resolutions = []
    loads = []

    def snapshot(**kwargs):
        resolutions.append(kwargs)
        return str(tmp_path)

    def load(path, **kwargs):
        loads.append((path, kwargs))
        return SimpleNamespace(predict=lambda *args: copy.deepcopy(raw_response))

    modules = {
        "laya_mlx": SimpleNamespace(load=load),
        "mlx.core": SimpleNamespace(metal=SimpleNamespace(is_available=lambda: True)),
        "huggingface_hub": SimpleNamespace(snapshot_download=snapshot),
    }
    monkeypatch.setattr(inference.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(inference.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(inference.platform, "mac_ver", lambda: ("14.0", (), ""))
    monkeypatch.setattr(inference.importlib, "import_module", lambda name: modules[name])
    monkeypatch.setattr(inference, "version", lambda name: "test")
    provider = LayaProvider(allow_download=allow_download)
    provider.predict(incident)
    provider.predict(incident)
    assert len(resolutions) == len(loads) == 1
    assert resolutions[0]["local_files_only"] is (not allow_download)
    assert resolutions[0]["token"] is False
    assert loads[0][0] == str(tmp_path.resolve())


def test_loading_failure_remains_error(monkeypatch, incident):
    def fail():
        raise OSError("broken checkpoint")

    provider = LayaProvider(agent_factory=fail)
    with pytest.raises(ProviderError) as caught:
        provider.predict(incident)
    assert caught.value.code == "load_failed"
    assert not provider.loaded
