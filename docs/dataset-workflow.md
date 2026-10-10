# Dataset v0.1: author, review, freeze, evaluate

This milestone implements the local workflow and seeds 25 individually authored synthetic drafts.
The supplied cases have **no completed human reviews** and **no frozen release**. Proposed causes
and rationales are hypotheses for you to review, not measured predictions or approved ground truth.
The existing 22 synthetic regression fixtures retain their original workflow.

## Files and format

Default workspace:

- `datasets/v0.1/drafts.jsonl`: schema version `1`, dataset version `0.1`, stable example and incident
  family IDs, `synthetic: true`, author/source/redaction provenance, question-version reference,
  bounded `state`, proposed cause, authored rationale, and evidence status.
- `datasets/v0.1/question-schema.json`: the current typed cause question, version
  `image-pull-cause-v1`, and explicit option order. Its structure, instructions, choices, and order
  must agree with the application contract. Question text/order changes require a new review basis.
- `datasets/v0.1/reviews.jsonl`: created by your first explicit review. Each event records the decision,
  final label, reviewer identity, aware UTC timestamp, notes, record hash, and question hash.
- `datasets/v0.1/review-packet.md`: self-contained evidence, proposed labels/rationales, provenance,
  current review status, latest review, and the complete typed question. Regenerate after reviews.

The pilot source format admits synthetic records only. Real evidence ingestion and broader dataset
versions require a separately scoped format extension; no real incidents were invented or imported.
JSON/JSONL readers reject duplicate JSON keys, non-finite constants, malformed records, oversized
files, unknown fields, and unknown taxonomy values. Evidence uses the existing incident limits.
Files are bounded to 8 MB, individual JSONL records to 64 KB, and source/review files to 1,000 entries.

Use the same family ID for all variants of an incident, including paraphrases and derived records.
Unique example IDs identify variants. Validation rejects identical normalized evidence in different
families; semantic near-duplicates still need human grouping. Shared error phrases across genuinely
different incidents are not enough to establish identical incident families.

## Your review

```sh
uv run --locked k8s-triage dataset validate
uv run --locked k8s-triage dataset review-packet --output datasets/v0.1/review-packet.md
```

Read each case's evidence and proposed rationale. Determine whether the evidence establishes one
of the four specific classes or belongs in the final category. Distinguish explicit other causes,
insufficient evidence, and unresolved competing signals. The draft evidence status is an authored
annotation, not a result from the rules provider.

After reviewing a case, record your decision. Replace the identity/note placeholders with your own
identity and evidence-based rationale; the CLI records these declarations but does not authenticate
the reviewer or prove that review occurred:

```sh
uv run --locked k8s-triage dataset review \
  --example-id v01-removed-catalog-tag --decision approved --label image_reference \
  --reviewer "YOUR_NAME" --note "YOUR_REVIEW_RATIONALE"
```

Approval always requires a supplied final label, reviewer, and nonblank note. There is no inferred
label, batch auto-approval, or provider-assisted approval. To correct a label, append another approved
decision with the corrected label and a rationale explaining it. The original proposal is preserved;
the latest event in append order supplies the final answer. To reject a case:

```sh
uv run --locked k8s-triage dataset review \
  --example-id v01-local-layer-permission --decision rejected \
  --reviewer "YOUR_NAME" --note "YOUR_REJECTION_REASON"
```

A rejected record blocks freezing until you revise/adjudicate it and explicitly approve it. Keep
reviewed example IDs in the source so log history remains attributable. When evidence, rationale,
proposal, provenance, or question changes, previous decisions become stale. Regenerate the packet,
review the changed case, then append a fresh decision; never rewrite old events. JSON formatting alone
does not invalidate approval, because hashes use normalized record content. Unknown review IDs and
duplicate event IDs are errors. POSIX advisory locking and fsync protect CLI append operations on
Mac/Linux; the prototype does not implement review appends on Windows.

`validate` exits 0 for structurally valid pending/rejected drafts and reports that a release cannot be
made. Stale reviews or inconsistent approved family labels exit 2. Malformed sources/logs also exit 2.
`review_status`, final approved-family counts, `release_ready`, and `release_blockers` explain the gate.

## Freeze a reviewed release

```sh
uv run --locked k8s-triage dataset freeze --output datasets/releases/v0.1
```

Every example must have a current approval. This pilot requires exactly 25 families and five families
per final cause, with one adjudicated cause per family. Corrections can change class coverage; revise
the corpus and obtain fresh reviews rather than relabeling evidence merely to satisfy balance or
splitting related examples into different families. Retain grouping and lineage when revising drafts.

Family IDs are sorted within each final cause, shuffled using seed 42 in the fixed cause order, then
assigned three families to train, one to calibration, and one to test per cause. This yields 15/5/5
families. Variant counts may make example counts differ from family counts; every variant stays in
its family's split. Source record order does not affect assignments.

Freeze exclusively creates a new directory and refuses even an empty existing directory. It writes
reviewed records (draft plus latest approval), the question snapshot, deterministic split manifest,
and a release manifest containing dataset/split/question hashes and file checksums. The manifest is
written last; incomplete output cannot be evaluated. Finished files/directories are read-only. To
revise a release, create a new output directory from newly reviewed source; do not edit it in place.

These are integrity checks against the local manifest, not cryptographic signatures or authentication
of reviewers. Filesystem owners can change permissions and manifests; the tool prevents accidental
overwriting and verifies consistent content before inference.

## Evaluate only a verified split

```sh
uv run --locked k8s-triage evaluate --provider rules \
  --dataset datasets/releases/v0.1 --split test \
  --report reports/dataset-rules.md --json-report reports/dataset-rules.json

# Uses the previously documented cached checkpoint; no download flag is supplied.
uv run --locked --extra laya k8s-triage evaluate --provider laya \
  --dataset datasets/releases/v0.1 --split test \
  --report reports/dataset-laya.md --json-report reports/dataset-laya.json
```

`--dataset` and `--fixtures` are mutually exclusive. Dataset evaluation requires an explicit split;
draft folders are not releases. The loader checks file hashes, question/runtime compatibility,
current embedded approvals, balanced grouped assignments, and record uniqueness before prediction.
Only the bounded incident reaches the provider. Scoring uses the human-approved final label and
review note, not the preserved proposal. Reports retain the reviewed source, reviewer metadata,
dataset/split/question hashes, errors, timing, and raw model responses.

Do not use the synthetic pilot as an independent production accuracy benchmark. Reserve fresh,
independently reviewed incident families for later evaluation, and do not tune against a test set
while continuing to call it unseen. No training stack, calibration fit, model download, or cluster
integration is part of the dataset commands.

## Verification

The milestone checks include correction/rejection history, stale record/question reviews, grouped
variants, deterministic class-balanced splits, frozen content/policy tampering, provider isolation,
CLI argument validation, review-packet/source preservation, and report provenance. Test-only approvals
and releases are confined to temporary pytest directories; they are not reviews of the delivered corpus.

```sh
uv run --locked pytest -q
uv run --locked ruff check src tests
uv run --locked ruff format --check src tests
```
