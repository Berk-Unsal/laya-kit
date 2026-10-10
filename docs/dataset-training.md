# Dataset development and future training

No training stack is installed in this application environment, and no training is run in this phase.
`laya-mlx` is the native inference/conversion runtime. Upstream Laya's custom decision architecture
uses PyTorch training; generic `mlx-lm` LoRA tooling is not assumed compatible.

## Next concrete step

The [dataset workflow](dataset-workflow.md) and 25 synthetic draft families are now implemented.
Review the [supplied packet](../datasets/v0.1/review-packet.md), record explicit approvals/corrections,
then freeze dataset v0.1 using the CLI. Every shipped record is initially pending; no human review
or frozen release was fabricated. This milestone targets five families per answer category.
For a later corpus, use authorized, redacted real incident evidence where available and mark synthetic
records honestly; this pilot's source format accepts synthetic records only.
Include missing-manifest versus access-denied contrasts, network versus TLS-trust failures, rate
limits despite successful authentication, explicit other causes, and unresolved multi-cause cases.
Record disagreements and adjudicate the correct diagnostic category before freezing dataset v0.1.
Do not turn the model's predictions into labels. These 22 regression cases remain smoke tests.

Versioned source records contain IDs, provenance, synthetic status, bounded state, proposed label,
rationale, evidence status, and a reference to the dataset-level typed question snapshot. Reviewer
identity, adjudicated final label, rationale, and status come from the separate append-only review log.
Frozen records contain the source plus its current approval; labels never enter state.

Freeze the question schema/version together with the dataset. Reject examples with labels/rationales
embedded accidentally in state. A future export adapter maps reviewed answers to the pinned upstream
trainer's `gold` representation; verify that representation against the chosen source revision before
writing a training exporter. The upstream MPS wrapper currently reads row-level JSONL containing
`state`, `questions`, and `gold` and delegates to `laya.train`; it is not a substitute for this project's
reviewed source format or grouped split policy.

## Splits and evaluation

Assign entire incident families to one split. Group paraphrases, repeated messages, tag substitutions,
shared incident timelines, and derived variants together; exact deduplication alone is insufficient.
Create versioned split manifests before tokenization. The pilot implements 60% training,
20% calibration, 20% test by family: three/one/one families per final cause. Twenty-five families are a pilot
corpus, not an adequate basis for broad accuracy claims; expand after reviewing class coverage.
Reserve additional newly authored, unseen test families beyond both the training pilot and these
regression fixtures. Do not use test errors to tune the same model and keep calling that set unseen.

Compare on exactly the same evidence:

| Candidate | Required comparison |
|---|---|
| Rules | No invented probability or calibration metrics |
| Unchanged Laya | Pinned checkpoint/runtime/question version |
| Fine-tuned Laya | Same inputs/options; training and calibration provenance recorded |

Report total/attempted/valid counts, errors and coverage, accuracy, per-class confusion/recall,
high-probability wrong selections (predeclared bins such as ≥0.8 and ≥0.9), and mistakes on explicit
other versus incomplete/conflicting subsets. For probabilistic providers, calculate multiclass Brier
score, log loss with documented clipping, reliability bins and expected calibration error. Fit any
temperature on calibration families only; evaluate frozen calibration on the untouched test set.
Model confidence must not automatically remove human review.

Run fixed option-order permutations and report label flips and probability shifts, including near
ties and option-token collisions. Preserve prompt schema, token loss, precision, model/source hashes,
all raw responses, and seed/split manifests. Measure cold load and first prediction separately from
warm prediction p50/p95, using sequential calls, explicit warmup, repeated runs, identical lengths and
machine/runtime details. The prototype report median includes the first prediction in its sequence;
it is not a warmed benchmark.

## Separate training environment (design only)

When training is authorized, create a separate `training/` project with its own Python 3.12 virtual
environment and lockfile. Pin a reviewed [upstream Laya source revision](https://github.com/NandhaKishorM/laya),
then resolve a mutually compatible PyTorch, Transformers, tokenizer, NumPy and safetensors stack.
Verify import/forward/backward and MPS support on the M4 before selecting exact pins. The current
[upstream package](https://github.com/NandhaKishorM/laya/blob/main/pyproject.toml) declares PyTorch
and Transformers dependencies; the [MPS script](https://github.com/NandhaKishorM/laya/blob/main/notebooks/laya_finetune_typed_decisions_mps.py)
provides a local path. Those training dependencies have not been compatibility-tested here and
must not be copied into the inference lockfile. No paid API, cloud GPU, dataset download, or automatic
Hub publication belongs in the pilot.

Start with a small **head-only pilot**: freeze encoder parameters, train the decision head/scorer and
the required typed embeddings after inspecting upstream parameter names and loss implementation.
Assert the freeze and count trainable parameters. The standard upstream wrapper is not assumed to
offer that mode; adapt a reviewed training loop if necessary. Keep the original 512-token inference
layout/context budget for the first pilot rather than copying a wrapper's larger context settings.
Use a small micro-batch, measured memory, deterministic seeds, conservative update budget, and early
stopping selected without test-set access. Freeze encoder gradients before considering full tuning.

Only consider broader fine-tuning after the pilot improves fresh grouped results and high-probability
error behavior without unacceptable latency or memory cost. Keep rules as the baseline even if the
specialist does not win.

## Return to native inference

Save weights, tokenizer, encoder/agent config, source revision, training recipe, dataset/split hashes,
and calibration provenance. Use the native runtime's documented `laya-mlx convert` pathway in a
separate conversion environment (it may need reference PyTorch dependencies); conversion changes
names/dtype and does not retrain the checkpoint.

Before deployment, compare PyTorch and MLX on the same frozen parity corpus: selected labels,
probability tolerances, option order, truncation/tokenization, calibration configuration, finite
repeated results, and memory/latency. Check FP32 first, then intended FP16 deployment. Explain every
disagreement or block deployment. Do not publish weights or change review policy as part of this plan.
