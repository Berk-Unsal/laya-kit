# Kubernetes Incident Triage

Local, offline-first decision support for image-pull failures. Submit incident evidence; receive a
selected cause, a ranked probability distribution when available, and an authored next diagnostic
check. **Every result requires human review.** A model probability is not verified correctness.

## Setup

Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/) are required. This checkout
has `.venv`, `uv.lock`, and a local Git repository with no remote. uv was installed at
`~/.local/bin/uv`; if it is not on your shell's PATH:

```sh
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.12
uv sync --locked
uv run --locked pytest -q
```

The portable installation includes rules, API, CLI, and development checks. It does not install MLX
or download model weights. For native inference on Apple Silicon, macOS 14+:

```sh
uv sync --locked --extra laya
```

This pins `laya-mlx==0.4.0` and locks its inference dependencies. PyTorch and training dependencies
are intentionally separate; see [training and dataset plan](docs/dataset-training.md).

## Predict

```sh
uv run --locked k8s-triage predict --provider rules --input examples/manifest_unknown.json

# Explicit first-use smoke test: may download the public checkpoint.
uv run --locked --extra laya k8s-triage predict --provider laya \
  --input examples/manifest_unknown.json --allow-download

# Cached weights only; no model network access.
uv run --locked --extra laya k8s-triage predict --provider laya \
  --input examples/manifest_unknown.json
```

`--input -` reads bounded incident JSON from stdin. The default checkpoint is `aac6fef/laya-mlx`,
pinned at `20aed815fc6acde75733882e7ec0e3f28aeb9717`. `--model /absolute/path/to/checkpoint` supports
an exported local checkpoint; its Hub revision is reported as unavailable. Another public Hub model
requires an appropriate `--revision`. No fallback provider is substituted if loading or inference fails.

Incident JSON contains only `events` (reason/message), `waiting` (reason/message/image), `images`,
and optional `log_excerpts`. Labels and reference rationales belong only in fixture records.
Input bounds: 32 events, 16 waiting states, 16 images, 8 log excerpts; messages 2,048 characters,
reasons 256, images 512, and combined normalized evidence 24,000 UTF-8 bytes. Empty evidence,
unknown fields, and oversized input are rejected. A valid image name alone is accepted as incomplete
evidence; it does not establish a failure cause.

## API

```sh
uv run --locked k8s-triage serve
# Default: http://127.0.0.1:8000; Ctrl-C stops it.
curl http://127.0.0.1:8000/health
curl -H 'Content-Type: application/json' http://127.0.0.1:8000/predict \
  -d '{"provider":"rules","incident":{"events":[{"message":"manifest unknown"}]}}'
```

For Laya requests, start with `uv run --locked --extra laya k8s-triage serve` after the explicit smoke
test has cached the checkpoint, and use `"provider":"laya"`. `serve --allow-download` is an explicit
server-wide opt-in to public checkpoint fetching on prediction. No request can enable downloads.
`GET /health` reports process health and whether Laya is loaded; it never imports MLX or loads weights.
It does not assert that inference is ready. `POST /predict` has a 64,000-byte body limit, including
chunked requests. Validation errors return 422, body-limit errors 413, backend availability/loading
errors 503, and invalid model responses/inference errors 502. `/docs` exposes the schema.

## Causes and contract

| Label | Description |
|---|---|
| `image_reference` | Invalid reference, absent image/tag, or missing platform manifest |
| `registry_auth` | Registry authentication or authorization failure |
| `registry_connectivity` | Registry DNS, timeout, or connection refusal |
| `registry_rate_limit` | Registry pull/request rate limiting |
| `other_or_insufficient_evidence` | A different cause, incomplete evidence, or competing signals |

`evidence_assessment.status` separately describes `specific_signal`, `other_signal`,
`insufficient_evidence`, or `conflicting_signals`, based on the authored rules. It is evidence
annotation, not model reasoning or a correctness estimate. A strong model preference for the final
label does not mean uncertainty about that label; for example, explicit disk exhaustion and an
unexplained backoff both select it under rules, with different evidence statuses.

Rules recognize explicit text such as `manifest unknown`, `unauthorized`, `connection refused`,
and HTTP 429. Competing category signals select the final label; ImagePullBackOff alone does too.
Image names are not scanned for error keywords. The baseline is lexical: it cannot reliably resolve
negation, quoted history, multilingual text, or causes spanning different containers/times. Provide
one coherent incident; manually correlate ambiguous records.

Outputs identify provider, checkpoint/revision, runtime, execution kind, selected cause, all five
probabilities and ranking when available, the mapped diagnostic check, timing, and mandatory review.
Rules return `null` probabilities/ranking; they invent no distribution. Laya validates labels,
numeric ranges, rounded distribution totals, and consistency with the selected answer, preserving
its full raw response and `usage`. `explanation_kind="authored_template"` explicitly marks the brief
application text. The upstream action head is retained only in raw evidence and is never executed.

## Evaluate and export

```sh
uv run --locked k8s-triage evaluate --provider rules \
  --report reports/rules.md --json-report reports/rules.json
uv run --locked --extra laya k8s-triage evaluate --provider laya \
  --report reports/laya.md --json-report reports/laya.json
uv run --locked ruff check src tests
uv run --locked ruff format --check src tests
```

There are **22 manually authored synthetic fixtures**, with grouped variants, contrast cases,
incomplete evidence, explicit other causes, and conflicts. They are regression/smoke checks, not
a sufficient training dataset or an independent production-quality benchmark. Reports are
self-contained Markdown with evidence, gold labels/rationales, predictions, errors, latency, and
raw responses. JSON export supports later analysis. Invalid/duplicate fixtures are `unevaluated`;
provider failures are `error`; neither counts as a valid prediction. Reports include both accuracy
among valid predictions and correct/attempted (failures count against that fraction). Exit 2 means
input/backend failure or evaluation errors/unevaluated cases; valid classification mistakes are
reported in scoring rather than treated as process failures.

Actual first-run results and full responses: [verification record](docs/verification.md),
[rules report](docs/evaluation/rules.md), [real Laya report](docs/evaluation/laya.md).
No simulated test outputs are included in those measurement reports.

## Scope and next phases

No cluster access, kubeconfig reads, Kubernetes credentials, command execution, generated remediation,
automatic changes, paid APIs, or dashboard. After dependencies and the checkpoint are cached,
predictions run locally. Evidence is held in memory; CLI report export writes only the requested files.
Installation needs package access unless your uv cache is already populated.

The base English checkpoint has a 512-token budget shared by evidence and choices; bounded JSON
can still exceed it. Inspect `usage.truncated`, `state_tokens_dropped`, and `usage.options` for lost
evidence/option distinctions. Review remains required even for untruncated, high-probability answers.

See [product/architecture and roadmap](docs/architecture.md) and
[dataset/training design](docs/dataset-training.md). Fine-tuning must beat rules and unchanged Laya
on fresh grouped holdouts before it earns a deployment role.
