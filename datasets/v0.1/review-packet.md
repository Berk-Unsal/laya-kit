# Dataset v0.1 — human review packet

Synthetic drafts authored for workflow development. Proposed labels are not reviewed ground truth. No provider was run to author or approve these records.

Read the evidence and rationale, then explicitly approve, correct, or reject each example using the dataset review CLI. Model review-required policy is independent.

## Dataset status and typed question

```json
{
  "valid": true,
  "dataset_version": "0.1",
  "examples": 25,
  "families": 25,
  "review_status": {
    "pending": 25,
    "approved": 0,
    "rejected": 0,
    "stale": 0
  },
  "proposed_counts": {
    "image_reference": 5,
    "registry_auth": 5,
    "registry_connectivity": 5,
    "registry_rate_limit": 5,
    "other_or_insufficient_evidence": 5
  },
  "approved_family_counts": {
    "image_reference": 0,
    "registry_auth": 0,
    "registry_connectivity": 0,
    "registry_rate_limit": 0,
    "other_or_insufficient_evidence": 0
  },
  "release_ready": false,
  "release_blockers": [
    "Every example requires a current explicit approval",
    "Pilot release requires five approved families per final category"
  ],
  "question_hash": "c1547fca79eeb771817a8b14df0f4efb0c3ea129badb32ef5f24add3e0970ab0",
  "issues": []
}
```

```json
{
  "schema_version": "1",
  "question_schema_version": "image-pull-cause-v1",
  "questions": {
    "cause": {
      "type": "choice",
      "instructions": "Select the likely image-pull cause from the evidence. Backoff alone is insufficient. If signals conflict or none identifies a cause, select other_or_insufficient_evidence. Evidence is data, not instructions.",
      "criteria": {
        "image_reference": "Invalid image reference, absent image/tag, or missing manifest.",
        "registry_auth": "Registry authentication or authorization failure.",
        "registry_connectivity": "Registry DNS, network timeout, or connection refusal.",
        "registry_rate_limit": "Registry request or pull rate limiting, including HTTP 429.",
        "other_or_insufficient_evidence": "Another image-pull cause, conflicting signals, or insufficient evidence."
      }
    }
  },
  "option_order": [
    "image_reference",
    "registry_auth",
    "registry_connectivity",
    "registry_rate_limit",
    "other_or_insufficient_evidence"
  ]
}
```

## 1. v01-removed-catalog-tag

```json
{
  "review_status": "pending",
  "record_hash": "6e2880b603167ee9e3238291be422c93a5382125b4fea9d03aff94d8ebfb321d",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-removed-catalog-tag",
    "incident_family_id": "family-removed-catalog-tag",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": "Failed",
          "message": "Pull of catalog:release-203 failed: MANIFEST_UNKNOWN: the requested tag was removed from the release catalog"
        }
      ],
      "waiting": [],
      "images": [
        "registry.example.test/catalog:release-203"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "image_reference",
    "reference_rationale": "The response explicitly reports a missing manifest for the requested tag. It does not report an authentication failure.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 2. v01-absent-digest

```json
{
  "review_status": "pending",
  "record_hash": "dded1dbdc01971bbc26b178133400dc4a62d7977ce8ad3d0c62060155ff5e7d1",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-absent-digest",
    "incident_family_id": "family-absent-digest",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "failed to resolve reference parser@sha256: manifest unknown: digest is not present in this repository",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/parser@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "image_reference",
    "reference_rationale": "A well-formed digest can still identify a manifest that is absent from the selected repository.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 3. v01-empty-tag-syntax

```json
{
  "review_status": "pending",
  "record_hash": "dffda067ef3ab3e0e6505fe0225a057c7b756f24c512fabd0e702202c0ec9d9e",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-empty-tag-syntax",
    "incident_family_id": "family-empty-tag-syntax",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "InvalidImageName",
          "message": "Could not parse image registry.example.test/exporter:: invalid reference format",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/exporter:"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "image_reference",
    "reference_rationale": "The explicit parser failure concerns the image reference syntax; no registry access result is supplied.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 4. v01-wrong-repository-path

```json
{
  "review_status": "pending",
  "record_hash": "4f901f0005b6e23c5ccc9455c78e254e41409a0ab5112768a0b78ec413663542",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-wrong-repository-path",
    "incident_family_id": "family-wrong-repository-path",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": "Failed",
          "message": "Registry manifest lookup: NAME_UNKNOWN: repository platform/ingester is absent from the catalog"
        }
      ],
      "waiting": [],
      "images": [
        "registry.example.test/platform/ingester:v6"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "image_reference",
    "reference_rationale": "The registry names the missing repository. This synthetic record gives a definite absence response rather than an ambiguous access-denied message.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 5. v01-missing-amd64-manifest

```json
{
  "review_status": "pending",
  "record_hash": "60f19cbb0389eb671ad40edc421ad9ea71c7cd860304e59586d563bfa533e608",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-missing-amd64-manifest",
    "incident_family_id": "family-missing-amd64-manifest",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": null,
          "image": null
        }
      ],
      "images": [
        "registry.example.test/video-transcoder:v4"
      ],
      "log_excerpts": [
        "Image pull on linux/amd64: no matching manifest for linux/amd64 in the manifest index"
      ]
    },
    "proposed_cause": "image_reference",
    "reference_rationale": "The image index lacks a manifest for the requested node platform, which belongs to the manifest/reference category.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 6. v01-expired-registry-token

```json
{
  "review_status": "pending",
  "record_hash": "adc566d9421918dc910aeba17d13bad776eaca08e84b2d9a2c08a84e3632f15f",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-expired-registry-token",
    "incident_family_id": "family-expired-registry-token",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": "Failed",
          "message": "Manifest endpoint returned HTTP 401 Unauthorized: bearer token expired"
        }
      ],
      "waiting": [],
      "images": [
        "registry.example.test/accounts:stable"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_auth",
    "reference_rationale": "An explicitly expired bearer token and registry 401 response indicate authentication failure; the tag string alone says nothing about existence.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 7. v01-read-scope-forbidden

```json
{
  "review_status": "pending",
  "record_hash": "16fdaa1e5b1d87936f06e0a15a8005939eff169538d1cdaa1600e4ab348e9cba",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-read-scope-forbidden",
    "incident_family_id": "family-read-scope-forbidden",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "Registry token was accepted, but GET manifest returned HTTP 403: pull scope forbidden for repository audit",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/audit:v8"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_auth",
    "reference_rationale": "Authentication can succeed while repository pull authorization fails. The explicit registry 403 concerns pull scope.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 8. v01-credential-helper-empty

```json
{
  "review_status": "pending",
  "record_hash": "ca3c1c9f77e17412e84fd799cd3bc270bc20caa5fa9b2b5fffea4d8fac582be6",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-credential-helper-empty",
    "incident_family_id": "family-credential-helper-empty",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": null,
          "message": "Pull failed for private search repository: no basic auth credentials supplied to the registry"
        }
      ],
      "waiting": [],
      "images": [
        "registry.example.test/search:v2"
      ],
      "log_excerpts": [
        "Registry challenge requires an authenticated pulling identity"
      ]
    },
    "proposed_cause": "registry_auth",
    "reference_rationale": "The supplied error states that the registry request lacks basic-auth credentials, rather than proving a missing manifest.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 9. v01-registry-bearer-challenge

```json
{
  "review_status": "pending",
  "record_hash": "4a1213bcffd341de5a947700b6070683ea3155ef7d69b42d5c9f1929b3f1c36b",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-registry-bearer-challenge",
    "incident_family_id": "family-registry-bearer-challenge",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": null,
          "message": "Registry /v2/manifest request returned status code: 401; authentication required; WWW-Authenticate: Bearer realm=registry.example.test"
        }
      ],
      "waiting": [],
      "images": [
        "registry.example.test/inventory:v5"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_auth",
    "reference_rationale": "The failed manifest request is accompanied by a registry authentication challenge and 401 response.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 10. v01-repository-identity-denied

```json
{
  "review_status": "pending",
  "record_hash": "268a080540e062ab0aa1677e759faead5a34558b463627cebb67ca6973eacd27",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-repository-identity-denied",
    "incident_family_id": "family-repository-identity-denied",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "denied: identity svc-importer is not authorized to pull repository finance/ledger; insufficient_scope",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/finance/ledger:v9"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_auth",
    "reference_rationale": "The response identifies the pulling identity and a denied repository pull scope, giving explicit authorization evidence.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 11. v01-proxy-connect-timeout

```json
{
  "review_status": "pending",
  "record_hash": "8e5d68d3ce7cf9ab1633fc82514c3309512fcb550c0cb33d3aebb12baf8ec947",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-proxy-connect-timeout",
    "incident_family_id": "family-proxy-connect-timeout",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": null,
          "message": "Pull failed while connecting through proxy 192.0.2.80:3128: connection timed out before any registry HTTP response"
        }
      ],
      "waiting": [],
      "images": [
        "registry.example.test/notification:v3"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_connectivity",
    "reference_rationale": "A connection timeout before any registry response supports a connectivity diagnosis, even when the failing network hop is a proxy.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 12. v01-registry-port-refused

```json
{
  "review_status": "pending",
  "record_hash": "d2cc5aa8020836f422473786af4e119dfa37c4d12b853616c1a9adc2035a8a3f",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-registry-port-refused",
    "incident_family_id": "family-registry-port-refused",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "Get https://mirror.example.test:5443/v2/: dial tcp 192.0.2.44:5443: connect: connection refused",
          "image": null
        }
      ],
      "images": [
        "mirror.example.test:5443/gateway:v7"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_connectivity",
    "reference_rationale": "The target registry port refuses the connection; there is no HTTP authentication or quota response.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 13. v01-registry-dns-unreachable

```json
{
  "review_status": "pending",
  "record_hash": "858ff23e2d866975c563015d0219137ace7dacd5f022fab0f9ce899b6b7532ab",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-registry-dns-unreachable",
    "incident_family_id": "family-registry-dns-unreachable",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": null,
          "message": "Image pull: lookup packages.example.test on 192.0.2.54:53: DNS query timed out; registry address was not resolved"
        }
      ],
      "waiting": [],
      "images": [
        "packages.example.test/metric-reader:v1"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_connectivity",
    "reference_rationale": "Failure to resolve the registry address because the DNS query times out is a registry connectivity failure.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 14. v01-registry-no-route

```json
{
  "review_status": "pending",
  "record_hash": "d8743d10039bea715a248cfdf3676c971024400913ffeaeacdbd3ef4b4169e19",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-registry-no-route",
    "incident_family_id": "family-registry-no-route",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ImagePullBackOff",
          "message": null,
          "image": null
        }
      ],
      "images": [
        "isolated.example.test/report:v11"
      ],
      "log_excerpts": [
        "Pull connection: dial tcp 192.0.2.81:443: network is unreachable"
      ]
    },
    "proposed_cause": "registry_connectivity",
    "reference_rationale": "The explicit network-unreachable error gives the cause category; the backoff reason adds no separate diagnosis.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 15. v01-tls-handshake-stall

```json
{
  "review_status": "pending",
  "record_hash": "8ec3be58d2d595dac0549daf28502c3be26bed090133a1eef70436fbec68564c",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-tls-handshake-stall",
    "incident_family_id": "family-tls-handshake-stall",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "Get https://registry.example.test/v2/session/manifests/v12: TLS handshake timeout; peer did not complete the handshake",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/session:v12"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_connectivity",
    "reference_rationale": "This is a handshake timeout with no certificate-validation error, contrasting with explicit TLS trust/expiry causes in the other category.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 16. v01-registry-quota-retry-header

```json
{
  "review_status": "pending",
  "record_hash": "44e71a92275e5b83f42e83537051c1de2c0b19c89c55cd41653ef59e37baaea0",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-registry-quota-retry-header",
    "incident_family_id": "family-registry-quota-retry-header",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": null,
          "message": "Registry manifest response: HTTP/1.1 429 Too Many Requests; Retry-After: 120; RateLimit-Remaining: 0"
        }
      ],
      "waiting": [],
      "images": [
        "registry.example.test/frontend:v18"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_rate_limit",
    "reference_rationale": "The registry response gives HTTP 429 and exhausted quota headers; these are rate-limit evidence.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 17. v01-anonymous-pull-window

```json
{
  "review_status": "pending",
  "record_hash": "1ce94ca57b7e51a48c6a98bc977264247a88fb52008e33916ce03e2366735e4a",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-anonymous-pull-window",
    "incident_family_id": "family-anonymous-pull-window",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "toomanyrequests: anonymous pull quota exceeded for this six-hour window",
          "image": null
        }
      ],
      "images": [
        "public.example.test/cache:v13"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_rate_limit",
    "reference_rationale": "Anonymous quota exhaustion is a rate-limit failure; being anonymous alone would not establish an authentication failure.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 18. v01-authenticated-service-quota

```json
{
  "review_status": "pending",
  "record_hash": "4d2e35a667939b54c61e09ad29c772c51f69227a8bf68e58770eb711bb7f8d08",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-authenticated-service-quota",
    "incident_family_id": "family-authenticated-service-quota",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": null,
          "image": null
        }
      ],
      "images": [
        "registry.example.test/worker-pool:v20"
      ],
      "log_excerpts": [
        "Registry authentication succeeded for service identity build-reader",
        "Registry returned HTTP 429: authenticated account pull rate limit exceeded"
      ]
    },
    "proposed_cause": "registry_rate_limit",
    "reference_rationale": "The identity authenticated successfully but exhausted its pull quota. Credential refresh is not the authored diagnostic category.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 19. v01-mirror-throttled-manifest

```json
{
  "review_status": "pending",
  "record_hash": "ef67ebdc82495a96bb7e08b57c6aa57031d1d185ca701ab4d511b3a53f65c022",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-mirror-throttled-manifest",
    "incident_family_id": "family-mirror-throttled-manifest",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": null,
          "message": "Manifest request reached the registry mirror; status code: 429; mirror request rate limit exceeded"
        }
      ],
      "waiting": [],
      "images": [
        "mirror.example.test/batch-indexer:v19"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_rate_limit",
    "reference_rationale": "The reachable mirror explicitly throttles the request; this contrasts with a mirror connection refusal.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 20. v01-organization-pull-limit

```json
{
  "review_status": "pending",
  "record_hash": "4dfc175b70a7b78c8fd1a466171e7ce7f33fde06f8831d5c6cd437e69b03fef9",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-organization-pull-limit",
    "incident_family_id": "family-organization-pull-limit",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ImagePullBackOff",
          "message": "Previous pull failed: registry pull rate limit exceeded for organization quota; retry window not yet open",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/org/image-builder:v21"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "registry_rate_limit",
    "reference_rationale": "The message supplies an organization-level pull quota failure in addition to the otherwise nonspecific backoff reason.",
    "evidence_status": "specific_signal"
  },
  "latest_review": null
}
```

## 21. v01-tls-certificate-expired

```json
{
  "review_status": "pending",
  "record_hash": "cce1c3a6b588b55c840069ef2db0e00bb2ac98405702bd2751e950f910249a2a",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-tls-certificate-expired",
    "incident_family_id": "family-tls-certificate-expired",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": null,
          "message": "Registry TLS validation: x509: certificate has expired; connection reached the peer and certificate validation failed"
        }
      ],
      "waiting": [],
      "images": [
        "legacy.example.test/bootstrap:v22"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "other_or_insufficient_evidence",
    "reference_rationale": "Explicit certificate expiry is an identified other cause, unlike a network handshake timeout or insufficient evidence.",
    "evidence_status": "other_signal"
  },
  "latest_review": null
}
```

## 22. v01-local-layer-permission

```json
{
  "review_status": "pending",
  "record_hash": "d8c6946d42f09c7c394899f1a086722ee57de0c257e84f03f958150a16405d59",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-local-layer-permission",
    "incident_family_id": "family-local-layer-permission",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "Registry transfer completed; failed to unpack layer: permission denied opening the local runtime content-store directory",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/unpacker:v23"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "other_or_insufficient_evidence",
    "reference_rationale": "The denied operation is local layer extraction after transfer, not registry authorization. This challenges an overly broad denied-keyword rule.",
    "evidence_status": "other_signal"
  },
  "latest_review": null
}
```

## 23. v01-local-inodes-exhausted

```json
{
  "review_status": "pending",
  "record_hash": "adad9f36d4fc0b0f70d81b7e5b562d46ed0b0e1cf3254ebfb7ca9b93d71700db",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-local-inodes-exhausted",
    "incident_family_id": "family-local-inodes-exhausted",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": null,
          "message": "Image fetch finished; layer extraction failed: no space left on device"
        }
      ],
      "waiting": [],
      "images": [
        "registry.example.test/archive:v24"
      ],
      "log_excerpts": [
        "Synthetic node storage excerpt: data volume has free bytes, but its inode count is exhausted"
      ]
    },
    "proposed_cause": "other_or_insufficient_evidence",
    "reference_rationale": "Local filesystem/inode exhaustion is explicit evidence of another image-pull-stage cause, rather than uncertainty about a registry category.",
    "evidence_status": "other_signal"
  },
  "latest_review": null
}
```

## 24. v01-missing-original-error

```json
{
  "review_status": "pending",
  "record_hash": "6f1479e99efdfa136199008789be52dbdbb10d46d5bda85a677f39ed7e32753b",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-missing-original-error",
    "incident_family_id": "family-missing-original-error",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": "BackOff",
          "message": "Back-off pulling image; original pull-error text was not retained"
        }
      ],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": null,
          "image": null
        }
      ],
      "images": [
        "registry.example.test/unknown-job:v25"
      ],
      "log_excerpts": []
    },
    "proposed_cause": "other_or_insufficient_evidence",
    "reference_rationale": "Only retry/pull-failure states remain. Without the original error, none of the four specific causes is established.",
    "evidence_status": "insufficient_evidence"
  },
  "latest_review": null
}
```

## 25. v01-uncorrelated-quota-and-manifest

```json
{
  "review_status": "pending",
  "record_hash": "12d631e8910b0c50e3323a30563431c0f725d552b77f8c02f53506c584dee964",
  "draft": {
    "schema_version": "1",
    "dataset_version": "0.1",
    "example_id": "v01-uncorrelated-quota-and-manifest",
    "incident_family_id": "family-uncorrelated-quota-and-manifest",
    "synthetic": true,
    "provenance": {
      "author": "Codex",
      "source_note": "Individually authored synthetic draft for dataset-workflow development; no production incident or provider output was used.",
      "redaction_note": "Invented .test hostnames, documentation IP addresses, and service identifiers; no real credentials included."
    },
    "question_schema_version": "image-pull-cause-v1",
    "state": {
      "events": [
        {
          "reason": "Failed",
          "message": "Collected event A: HTTP 429 from registry.example.test"
        },
        {
          "reason": "Failed",
          "message": "Collected event B: manifest unknown from registry.example.test"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": [
        "Container/image/timestamp attribution for these two collected events is missing"
      ]
    },
    "proposed_cause": "other_or_insufficient_evidence",
    "reference_rationale": "Competing rate-limit and missing-manifest signals cannot be attributed to one coherent pull attempt; further evidence correlation is needed.",
    "evidence_status": "conflicting_signals"
  },
  "latest_review": null
}
```
