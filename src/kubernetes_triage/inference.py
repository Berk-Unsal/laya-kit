"""Lazy native Laya adapter. No MLX import, weight access, or download at module import."""

import importlib
import json
import platform
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from threading import Lock
from time import perf_counter

from pydantic import ValidationError

from .contract import CHECKS, explanation, model_questions, model_state
from .rules import assess_evidence
from .schemas import Cause, Incident, Prediction, RankedOption

DEFAULT_MODEL = "aac6fef/laya-mlx"
DEFAULT_REVISION = "20aed815fc6acde75733882e7ec0e3f28aeb9717"
CHECKPOINT_FILES = [
    "model.safetensors",
    "rl_agent_config.json",
    "encoder/config.json",
    "tokenizer/*",
    "mlx_config.json",
]


class ProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, raw_response=None, inference_ms=None):
        super().__init__(message)
        self.code = code
        self.raw_response = raw_response
        self.inference_ms = inference_ms


def parse_response(
    raw: object,
    incident: Incident,
    *,
    model: str,
    revision: str | None,
    runtime_version: str,
    inference_ms: float,
    model_load_ms: float = 0,
    injected: bool = False,
) -> Prediction:
    """Validate upstream's choice response without changing rounded probabilities."""
    try:
        if not isinstance(raw, dict):
            raise ValueError("Response must be a JSON object")
        # Enforce JSON compatibility, preserve the full returned response without selecting fields.
        json.dumps(raw, allow_nan=False)
        answers = raw["answers"]
        if not isinstance(answers, dict) or set(answers) != {"cause"}:
            raise ValueError("Response must answer exactly the supplied cause question")
        answer = answers["cause"]
        if answer["type"] != "choice":
            raise ValueError("Cause answer must have type choice")
        selected = Cause(answer["choice"])
        probs = answer["probabilities"]
        if not isinstance(probs, dict) or set(probs) != {c.value for c in Cause}:
            raise ValueError("Probability labels must match all supplied choices exactly")
        if any(isinstance(p, bool) or not isinstance(p, (int, float)) for p in probs.values()):
            raise ValueError("Probability values must be numbers, not booleans or strings")
        probabilities = {cause: probs[cause.value] for cause in Cause}
        ranked = [
            RankedOption(cause=c, probability=p)
            for c, p in sorted(probabilities.items(), key=lambda pair: -pair[1])
        ]
        usage = raw.get("usage")
        if not isinstance(usage, dict):
            raise ValueError("Response must preserve a usage object")
        assessment = assess_evidence(incident)
        return Prediction(
            provider="laya",
            execution_kind="injected_test" if injected else "native_mlx",
            model=model,
            model_revision=revision,
            runtime_version=runtime_version,
            dtype="float16",
            selected_cause=selected,
            probabilities=probabilities,
            ranked_options=ranked,
            evidence_assessment=assessment,
            recommended_check=CHECKS[selected],
            explanation=explanation(selected, assessment),
            inference_ms=inference_ms,
            model_load_ms=model_load_ms,
            usage=usage,
            raw_response=raw,
        )
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        # Non-JSON outputs have no lossless JSON representation; retain their repr as diagnostic data.
        try:
            json.dumps(raw, allow_nan=False)
            preserved = raw
        except (TypeError, ValueError):
            preserved = {"non_json_response_repr": repr(raw)}
        raise ProviderError(
            "invalid_response",
            f"Laya response rejected: {exc}",
            raw_response=preserved,
            inference_ms=inference_ms,
        ) from exc


class LayaProvider:
    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        revision: str | None = DEFAULT_REVISION,
        allow_download: bool = False,
        agent_factory: Callable | None = None,
    ):
        self.model = model
        self.revision = (
            None
            if (Path(model).expanduser().is_dir() or model.startswith(("/", "./", "../", "~")))
            else revision
        )
        self.allow_download = allow_download
        self._factory = agent_factory
        self._agent = None
        self._lock = Lock()
        self._runtime_version = "injected-test-agent" if agent_factory else "not_loaded"

    @property
    def loaded(self) -> bool:
        return self._agent is not None

    def _load_native(self):
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            raise ProviderError("unsupported_hardware", "Laya MLX requires an Apple Silicon Mac.")
        if int(platform.mac_ver()[0].split(".")[0] or 0) < 14:
            raise ProviderError("unsupported_hardware", "Laya MLX requires macOS 14 or newer.")
        try:
            laya = importlib.import_module("laya_mlx")
            mx = importlib.import_module("mlx.core")
            hub = importlib.import_module("huggingface_hub")
        except ImportError as exc:
            raise ProviderError(
                "missing_dependency",
                "Install optional inference dependencies with "
                "uv sync --extra laya on Apple Silicon.",
            ) from exc
        if not mx.metal.is_available():
            raise ProviderError(
                "unsupported_hardware", "MLX Metal GPU is unavailable in this process."
            )
        self._runtime_version = version("laya-mlx")
        local = Path(self.model).expanduser()
        try:
            if local.is_dir():
                checkpoint = local.resolve()
            elif self.model.startswith(("/", "./", "../", "~")):
                raise FileNotFoundError(f"Local checkpoint directory does not exist: {local}")
            else:
                checkpoint = Path(
                    hub.snapshot_download(
                        repo_id=self.model,
                        revision=self.revision,
                        local_files_only=not self.allow_download,
                        allow_patterns=CHECKPOINT_FILES,
                        token=False,  # Public checkpoint; no credentials are requested.
                    )
                ).resolve()
            # Loading an absolute resolved directory prevents a second implicit Hub fetch.
            return laya.load(str(checkpoint), dtype="float16", device="gpu")
        except Exception as exc:
            hint = (
                " An explicit CLI prediction with --allow-download may fetch the public checkpoint."
                if not self.allow_download
                else ""
            )
            raise ProviderError(
                "load_failed", f"Could not load {self.model}: {exc}.{hint}"
            ) from exc

    def predict(self, incident: Incident) -> Prediction:
        # A single resident agent; serialize native loading/inference for shared API callers.
        with self._lock:
            load_ms = 0.0
            if self._agent is None:
                start = perf_counter()
                try:
                    self._agent = self._factory() if self._factory else self._load_native()
                except ProviderError:
                    raise
                except Exception as exc:
                    raise ProviderError("load_failed", f"Laya loading failed: {exc}") from exc
                load_ms = (perf_counter() - start) * 1000
            start = perf_counter()
            try:
                raw = self._agent.predict(model_state(incident), model_questions())
            except Exception as exc:
                raise ProviderError(
                    "inference_failed",
                    f"Laya inference failed: {exc}",
                    inference_ms=(perf_counter() - start) * 1000,
                ) from exc
            elapsed = (perf_counter() - start) * 1000
            return parse_response(
                raw,
                incident,
                model=self.model,
                revision=self.revision,
                runtime_version=self._runtime_version,
                inference_ms=elapsed,
                model_load_ms=load_ms,
                injected=self._factory is not None,
            )
