# Product and architecture

Kubernetes Incident Triage helps a human decide what evidence to inspect next for an image-pull
failure. It accepts manually supplied evidence and chooses among five fixed causes. It neither
generates prose with a language model nor executes a diagnostic/remediation action.

## Boundaries

```text
incident JSON → bounded Pydantic schema → explicit provider
    rules → conservative lexical classification
    laya  → evidence-only state + authored typed question → resident MLX agent
          → validated choice and complete probability mapping
both → authored check mapping + evidence annotation + required human review

fixture evaluator → incident only → provider
                  → labels/rationales retained outside inference → report/scoring
```

The `src/kubernetes_triage` package keeps `schemas`, `contract`, `rules`, `inference`, `service`,
`evaluation`, `cli`, and `api` separate. The service owns one provider of each kind. Laya loads
lazily once per service process, with a lock around loading/inference; it is reused for API requests
and fixture runs. Multiple server workers would each load a model, so this prototype uses one.

The default is rules. Laya is selected explicitly and has no fallback. Offline checkpoint resolution
uses `snapshot_download(local_files_only=True)` followed by an absolute local directory passed to
`laya_mlx.load(..., dtype="float16", device="gpu")`. Explicit permission via the CLI download flag
changes only the public checkpoint fetch policy; imports, installation, tests, and health do not
download weights. Health does not check backend readiness. The CLI owns model configuration;
requests cannot select arbitrary models or checkpoint locations.

Five probabilities are required from Laya, checked for finite numeric values, label completeness,
range, normalization within four-decimal rounding tolerance, and selected-answer consistency.
The original probabilities are retained without renormalization. Stable ranking preserves choice
order for rounded ties. Raw responses include upstream confidence and action-head fields, but these
are not remediation instructions or review-policy inputs. Unsupported hardware, absent dependencies,
checkpoint loading, native inference, and response validation each have explicit errors.

`other_or_insufficient_evidence` is an answer, not a low-confidence sentinel. Independent lexical
evidence status separates explicit other causes, insufficient evidence, and conflicts. The model's
distribution describes its preference among labels, not verified correctness. The application always
requires human review and identifies explanations as authored templates.

Incident evidence has bounded lists/strings and a combined byte budget. HTTP also bounds the body
before JSON parsing. Ground truth is excluded by construction: the adapter accepts `Incident`,
while the evaluator owns `Fixture`. Evidence text may itself be adversarial, ambiguous, or mention
labels; the instruction treats it as data. This separation prevents structural label leakage and does
not claim universal immunity to misleading evidence.

## Phased roadmap

1. **Offline prototype (implemented):** bounded input, conservative rules, optional resident MLX,
   CLI/API, authored next checks, synthetic regressions, raw response and error reporting.
2. **Dataset development (workflow implemented; human review pending):** version and review a small
   domain corpus with incident-family IDs,
   source/provenance and redaction notes, explicit labels and evidence completeness. Expand contrast
   cases and adjudicate ambiguity; freeze grouped train/calibration/test manifests. Keep these 22
   regression fixtures outside the fresh test set.
3. **Training, calibration, evaluation:** compare rules, unchanged Laya, then a head-only PyTorch
   pilot. Evaluate grouped fresh holdouts, calibration, high-probability mistakes, order sensitivity,
   per-class failures, and latency. Consider wider training only after the pilot earns it. Convert
   candidate checkpoints back to MLX and verify inference parity before deployment.
4. **Optional read-only cluster integration:** a separately scoped evidence collector with explicit
   user-selected context and least-privilege read permissions. Preserve the same incident boundary
   and review policy. Cluster writes, automatic remediation, and command generation remain outside
   this product's decision-support role.

## Experiment context

The user reported an earlier broad synthetic Kubernetes experiment: 21/30 reference matches and
about 36.4 ms median inference, with some high-probability mistakes (including credential refresh
for a nonexistent tag). Its source cases/results were not present in this initially empty folder.
Those figures were not reproduced here and are preliminary observations, not production accuracy
claims. The new 22-case image-pull suite is separately authored and independently measured.

## Upstream verification

Checked 10 October 2026 against primary sources and the installed runtime:

- [Native runtime README](https://github.com/mizorewww/laya-mlx): typed `load`/`predict`, Apple
  Silicon/macOS 14+/Python 3.11+, separate inference and conversion role.
- [Agent implementation](https://github.com/mizorewww/laya-mlx/blob/v0.4.0/laya_mlx/agent.py):
  choice result structure, `usage` and truncation fields, local checkpoint loading.
- [Runtime package metadata](https://pypi.org/project/laya-mlx/0.4.0/): pinned release;
  MLX dependency compatibility resolved and recorded in `uv.lock`.
- [Checkpoint card](https://huggingface.co/aac6fef/laya-mlx): custom decision architecture,
  512-token context, FP16 conversion and provenance.
- [Upstream training script](https://github.com/NandhaKishorM/laya/blob/main/notebooks/laya_finetune_typed_decisions_mps.py):
  PyTorch MPS/CPU path, independent from MLX inference. No training was run.
