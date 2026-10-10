import json
import subprocess
import sys

from fastapi.testclient import TestClient

from kubernetes_triage.api import create_app
from kubernetes_triage.cli import main
from kubernetes_triage.evaluation import evaluate, markdown_report, write_reports
from kubernetes_triage.inference import ProviderError, parse_response
from kubernetes_triage.rules import RulesProvider
from kubernetes_triage.service import TriageService


def test_evaluation_does_not_score_errors_or_invalid_fixtures(records, tmp_path):
    calls = []

    def predict(incident):
        calls.append(incident)
        if len(calls) == 2:
            raise ProviderError(
                "invalid_response", "test rejection", raw_response={"bad": "value"}, inference_ms=3
            )
        return RulesProvider().predict(incident)

    report = evaluate(
        [records[0], records[1], {"broken": True}], predict, provider="rules", model="test"
    )
    summary = report["summary"]
    assert summary["valid"] == summary["correct"] == 1
    assert summary["errors"] == summary["unevaluated"] == 1
    assert summary["accuracy_valid"] == 1
    assert summary["correct_fraction_attempted"] == 0.5
    assert len(calls) == 2
    assert report["cases"][1]["prediction"] is None
    output = tmp_path / "report.md"
    data = tmp_path / "report.json"
    write_reports(report, output, data)
    text = output.read_text()
    assert '"bad": "value"' in text
    assert "manifest unknown" in text
    assert records[0]["reference_rationale"] in text
    assert json.loads(data.read_text()) == report


def test_no_valid_predictions_has_no_accuracy(records):
    def fail(incident):
        raise ProviderError("load_failed", "not available")

    report = evaluate([records[0]], fail, provider="laya", model="test")
    assert report["summary"]["accuracy_valid"] is None
    assert report["summary"]["median_inference_ms_valid"] is None
    assert report["summary"]["correct_fraction_attempted"] == 0


def test_duplicate_fixture_is_unevaluated(records):
    report = evaluate(
        [records[0], records[0]], RulesProvider().predict, provider="rules", model="test"
    )
    assert report["summary"]["valid"] == 1
    assert report["summary"]["unevaluated"] == 1


def test_high_probability_errors_are_exposed_and_simulations_marked(records, raw_response):
    record = records[4]  # auth reference, injected image-reference answer

    def predict(incident):
        return parse_response(
            raw_response,
            incident,
            model="test",
            revision=None,
            runtime_version="test",
            inference_ms=2,
            injected=True,
        )

    report = evaluate([record], predict, provider="laya", model="test")
    assert report["summary"]["accuracy_valid"] == 0
    assert report["summary"]["high_probability_mistakes_at_0_8"] == [record["id"]]
    assert report["summary"]["execution_kinds"] == {"injected_test": 1}
    assert '"extra_metadata"' in markdown_report(report)
    assert "simulations" in markdown_report(report)


def test_health_never_loads_model_and_rules_api_works(incident):
    service = TriageService()
    service.laya._factory = lambda: (_ for _ in ()).throw(AssertionError("unexpected model load"))
    with TestClient(create_app(service)) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert not health.json()["laya_loaded"]
        prediction = client.post(
            "/predict", json={"provider": "rules", "incident": incident.model_dump(mode="json")}
        )
        assert prediction.status_code == 200
        assert prediction.json()["selected_cause"] == "image_reference"
        assert prediction.json()["probabilities"] is None
        assert not service.laya.loaded


def test_api_validation_body_limits_and_model_error(incident):
    service = TriageService()

    def fail():
        raise ProviderError("missing_dependency", "install optional dependencies")

    service.laya._factory = fail
    with TestClient(create_app(service)) as client:
        assert client.post("/predict", json={"incident": {}}).status_code == 422
        assert client.post("/predict", json={"provider": "auto", "incident": {}}).status_code == 422
        assert client.post("/predict", content=b"x" * 64001).status_code == 413
        assert (
            client.post("/predict", content=iter([b"x" * 32000, b"x" * 32001])).status_code == 413
        )
        result = client.post(
            "/predict", json={"provider": "laya", "incident": incident.model_dump()}
        )
        assert result.status_code == 503
        assert result.json()["detail"]["code"] == "missing_dependency"
        assert result.json()["detail"]["review_status"] == "required"


def test_imports_and_rules_without_mlx():
    code = """
import sys
class BlockMLX:
    def find_spec(self, fullname, *args):
        if fullname.startswith(("mlx", "laya_mlx", "huggingface_hub")):
            raise AssertionError("Unexpected ML import: " + fullname)
sys.meta_path.insert(0, BlockMLX())
import kubernetes_triage.api
import kubernetes_triage.cli
from kubernetes_triage.schemas import Incident
from kubernetes_triage.rules import RulesProvider
assert RulesProvider().predict(Incident(images=["app:v1"])).review_status == "required"
"""
    subprocess.run([sys.executable, "-c", code], check=True)


def test_cli_prediction_evaluation_and_bad_input(records, tmp_path, capsys):
    source = tmp_path / "incident.json"
    source.write_text(json.dumps(records[0]["incident"]))
    assert main(["predict", "--input", str(source), "--provider", "rules"]) == 0
    assert json.loads(capsys.readouterr().out)["selected_cause"] == "image_reference"
    source.write_text("{}")
    assert main(["predict", "--input", str(source)]) == 2
    assert "invalid_input" in capsys.readouterr().err
    fixtures = tmp_path / "fixtures.json"
    fixtures.write_text(json.dumps([records[0], {"invalid": True}]))
    output = tmp_path / "report.md"
    assert main(["evaluate", "--fixtures", str(fixtures), "--report", str(output)]) == 2
    assert output.is_file()
    assert json.loads(capsys.readouterr().out)["unevaluated"] == 1


def test_cli_rejects_nonstandard_json_constants(tmp_path, capsys):
    source = tmp_path / "invalid.json"
    source.write_text('{"images":[NaN]}')
    assert main(["predict", "--input", str(source)]) == 2
    assert "Non-finite JSON constant" in capsys.readouterr().err
