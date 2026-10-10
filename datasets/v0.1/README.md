# Draft synthetic dataset v0.1

25 new incident families, one draft example per family, five proposed cases per cause. Each record
is explicitly synthetic and attributed to Codex. No provider output or real production incident was
used to author the proposals. No human approval or frozen release is supplied.

Start with [the review packet](review-packet.md), then follow [the review workflow](../../docs/dataset-workflow.md).
The review log appears only after you record a decision. Keep its history in version control along
with source and question changes. Never move these drafts into the existing regression fixture file.

Case coverage includes missing tags/digests/platform manifests, invalid references, explicit registry
access failures, proxy/port/DNS/network/handshake failures, anonymous/authenticated/mirror quotas,
certificate expiry, local layer permissions and inode exhaustion, missing original errors, and
uncorrelated competing failures. Proposed labels remain subject to your judgment.
