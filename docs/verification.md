# Executed verification — 10 October 2026

The initially empty folder was inspected before changes. A local Git repository was initialized;
no remote was configured. uv 0.13.0 was installed in `~/.local/bin` without changing shell profiles,
and uv installed Python 3.12.13 and created the project's `.venv` and `uv.lock`.

Machine: Apple M4, arm64, 24 GiB unified memory, macOS 27.0.1. Native inference:
`laya-mlx` 0.4.0, MLX 0.32.3, FP16, Metal GPU, public checkpoint `aac6fef/laya-mlx` revision
`20aed815fc6acde75733882e7ec0e3f28aeb9717`. No PyTorch/training stack was installed.

## Real execution results

The explicit Laya smoke prediction ran with `--allow-download` and resolved the public checkpoint
(the existing local cache could be reused). It produced a valid native response for
`examples/manifest_unknown.json`, selecting `other_or_insufficient_evidence` rather than the
reference `image_reference`. Smoke inference: 781.331 ms; loading: 1,727.196 ms. This verifies
execution, not a correct diagnosis. Its untouched prediction is in
[the native smoke artifact](evaluation/laya-smoke.json).

Then a sequential, cached-checkpoint evaluation ran on all 22 manually authored synthetic fixtures.
It used actual native predictions and no injected agents:

| Provider | Valid / attempted | Reference matches | Errors | Median inference |
|---|---:|---:|---:|---:|
| Rules | 22 / 22 | 22 / 22 | 0 | 0.0138 ms |
| Unchanged Laya | 22 / 22 | 12 / 22 | 0 | 53.790 ms |

Laya's run completed at 22:20:25 Europe/Istanbul on 10 October 2026. No cases reported state
truncation. The first prediction in that evaluation took 86.465 ms; its model load took 323.289 ms.
The median includes the first prediction, excludes loading, lock waiting and output validation, and
is not a warmed latency benchmark. Different process/cache/kernel state explains why the separate
first smoke has a different timing; no controlled repeated performance study was conducted.

Laya selected `registry_auth` on the conflicting manifest/auth fixture with probability **0.8876**,
against the reference `other_or_insufficient_evidence`. This is a recorded high-probability mistake,
not verified certainty. It also missed the manifest-unknown contrast, several network cases, and
other/ambiguous cases. The baseline outperformed unchanged Laya on this deliberately small suite.
The fixtures were authored alongside the rules and are not a blinded accuracy study or an adequate
fine-tuning dataset. These observations do not reproduce or extend the earlier absent 30-case benchmark.

Full evidence, references, predictions, timing, probabilities and raw responses are preserved in
[rules Markdown](evaluation/rules.md), [rules JSON](evaluation/rules.json),
[real Laya Markdown](evaluation/laya.md), and [real Laya JSON](evaluation/laya.json).
Report rendering was regenerated from the saved measurements to include the question schema and
environment metadata; predictions and recorded timing were retained.

## Portable and interface checks

- Pytest: 55 behavioral tests covering regression/contrast/conflict behavior, schema bounds,
  strict response parsing, full metadata preservation, load-once concurrency, offline resolution,
  missing dependencies/hardware/loading/inference errors, structural label isolation, report scoring,
  high-probability errors, invalid/duplicate fixture accounting, API validation/body limits, and CLI.
- A subprocess blocks imports of MLX, Laya-MLX and Hugging Face; rules and API/CLI imports still work.
- Ruff lint and formatting checks passed; `uv lock --check` passed.
- Actual loopback Uvicorn server on port 8765: `/health` 200 with Laya unloaded, rules `/predict` 200
  without loading Laya, native Laya `/predict` 200 followed by loaded health, invalid evidence 422.
  The temporary verification server was stopped afterward. See [HTTP artifact](evaluation/http-smoke.json).
- CLI rules prediction and both real fixture evaluations executed, exporting Markdown and JSON.

The installed Starlette TestClient emits a deprecation notice about its httpx adapter; tests and
real HTTP checks pass. This is not a failed check. No required phase-one check is blocked. Training,
fine-tuned comparisons/calibration, conversion parity, independent test accuracy, and cluster
integration are future work and were not executed.

The original next step was a reviewed dataset workflow; its implementation is recorded below.

## Dataset workflow milestone — 10 October 2026

Implemented `dataset validate`, `review-packet`, `review`, and `freeze`, plus verified frozen-dataset
evaluation with an explicit split. The shipped corpus contains 25 new individually authored synthetic
families, five proposed cases per category, all pending human review. No provider was used to author
or approve these records. No review log or frozen release was fabricated for the shipped corpus.

Executed checks:

- **106 pytest tests passed**: the original 55 plus 51 dataset cases, including invalid JSON/metadata,
  evidence bounds, duplicates, explicit correction/rejection history, stale approvals, question/order
  changes, concurrent log appends, grouped variants, deterministic 15/5/5 family splits, read-only
  releases, tamper detection, evaluation label isolation, and report provenance.
- Executed `uv sync --locked` to test the portable profile with **MLX and Laya-MLX absent**;
  the complete suite and dataset validation passed. Native inference remains available through the
  documented `--extra laya` profile; no weights were fetched or models run in this milestone.
- CLI validation reported 25 pending, zero approved/rejected/stale, balanced proposed categories,
  and `release_ready: false`. Regenerated the self-contained Markdown packet from the source.
- Existing CLI fixture evaluation still completed with 22 valid rules predictions and 22 reference
  matches; the smoke report is separate from the earlier saved measurements.
- Ruff lint/format, lockfile validation, and whitespace checks passed. The existing Starlette
  TestClient deprecation notice persists; no test failed.

Test-only decisions and frozen releases exist only in temporary test directories. There is no new
dataset accuracy claim. Freezing/evaluating the delivered corpus awaits your actual reviews by design.
Start with [the review packet](../datasets/v0.1/review-packet.md) and
[the workflow guide](dataset-workflow.md). Training and cluster integration remain deferred.
