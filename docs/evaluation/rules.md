# Kubernetes image-pull fixture evaluation

Manually authored synthetic regression fixtures; not a production accuracy estimate or a sufficient training dataset. All predictions require human review.

Latency covers rules classification or Laya evidence preparation plus synchronized predict, excluding output validation, checkpoint loading, and lock wait. First-load time is recorded separately. No probabilities are invented for rules.

Injected test-agent outputs, if present, are simulations and are not real model measurements. Errors and unevaluated fixtures are not valid predictions.

## Run and scoring

```json
{
  "created_at": "2026-10-10T19:18:49.710536+00:00",
  "provider": "rules",
  "model": "image-pull-rules-v1",
  "summary": {
    "total": 22,
    "attempted": 22,
    "valid": 22,
    "correct": 22,
    "errors": 0,
    "unevaluated": 0,
    "accuracy_valid": 1.0,
    "correct_fraction_attempted": 1.0,
    "median_inference_ms_valid": 0.01377049193251878,
    "execution_kinds": {
      "deterministic": 22
    },
    "high_probability_mistakes_at_0_8": [],
    "per_class": {
      "image_reference": {
        "valid": 4,
        "correct": 4
      },
      "registry_auth": {
        "valid": 4,
        "correct": 4
      },
      "registry_connectivity": {
        "valid": 4,
        "correct": 4
      },
      "registry_rate_limit": {
        "valid": 4,
        "correct": 4
      },
      "other_or_insufficient_evidence": {
        "valid": 6,
        "correct": 6
      }
    }
  },
  "environment": {
    "python": "3.12.13",
    "os": "macOS-27.0.1-arm64-arm-64bit",
    "machine": "arm64"
  },
  "question_schema": null
}
```

## Case 1

```json
{
  "id": "manifest-unknown",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "manifest-unknown",
    "group_id": "missing-release-tag",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": "Failed",
          "message": "Failed to pull image: manifest unknown: manifest unknown"
        }
      ],
      "waiting": [
        {
          "reason": "ImagePullBackOff",
          "message": null,
          "image": null
        }
      ],
      "images": [
        "registry.example.test/payments:release-404"
      ],
      "log_excerpts": []
    },
    "expected_cause": "image_reference",
    "reference_rationale": "Manifest unknown explicitly identifies an absent manifest; backoff supplies no alternate cause."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "image_reference",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "image_reference"
    ]
  },
  "recommended_check": {
    "id": "verify_image_manifest",
    "title": "Verify the image reference and manifest",
    "description": "Compare the exact registry, repository, tag or digest with the publisher's catalog and supported platforms. Check whether that manifest exists."
  },
  "inference_ms": 0.02941599814221263,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Invalid image reference, absent image/tag, or missing manifest. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 2

```json
{
  "id": "tag-not-found",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "tag-not-found",
    "group_id": "missing-release-tag",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "image tag release-404 not found in registry",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/payments:release-404"
      ],
      "log_excerpts": []
    },
    "expected_cause": "image_reference",
    "reference_rationale": "The named image tag is absent; credential refresh is not supported by this evidence."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "image_reference",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "image_reference"
    ]
  },
  "recommended_check": {
    "id": "verify_image_manifest",
    "title": "Verify the image reference and manifest",
    "description": "Compare the exact registry, repository, tag or digest with the publisher's catalog and supported platforms. Check whether that manifest exists."
  },
  "inference_ms": 0.015124998753890395,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Invalid image reference, absent image/tag, or missing manifest. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 3

```json
{
  "id": "invalid-reference",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "invalid-reference",
    "group_id": "malformed-reference",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [
        {
          "reason": "InvalidImageName",
          "message": "Failed to apply default image tag: invalid reference format",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/APP:bad tag"
      ],
      "log_excerpts": []
    },
    "expected_cause": "image_reference",
    "reference_rationale": "The runtime explicitly rejects the reference syntax."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "image_reference",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "image_reference"
    ]
  },
  "recommended_check": {
    "id": "verify_image_manifest",
    "title": "Verify the image reference and manifest",
    "description": "Compare the exact registry, repository, tag or digest with the publisher's catalog and supported platforms. Check whether that manifest exists."
  },
  "inference_ms": 0.01333298860117793,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Invalid image reference, absent image/tag, or missing manifest. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 4

```json
{
  "id": "platform-manifest",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "platform-manifest",
    "group_id": "platform-manifest",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "no matching manifest for linux/arm64/v8 in the manifest list entries"
        }
      ],
      "waiting": [],
      "images": [
        "registry.example.test/worker:1.0"
      ],
      "log_excerpts": []
    },
    "expected_cause": "image_reference",
    "reference_rationale": "The platform-specific manifest is missing, even if another platform's image exists."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "image_reference",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "image_reference"
    ]
  },
  "recommended_check": {
    "id": "verify_image_manifest",
    "title": "Verify the image reference and manifest",
    "description": "Compare the exact registry, repository, tag or digest with the publisher's catalog and supported platforms. Check whether that manifest exists."
  },
  "inference_ms": 0.014792007277719676,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Invalid image reference, absent image/tag, or missing manifest. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 5

```json
{
  "id": "unauthorized-existing-tag",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "unauthorized-existing-tag",
    "group_id": "private-repository-access",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "failed to authorize: HTTP 401 Unauthorized",
          "image": null
        }
      ],
      "images": [
        "registry.example.test/payments:release-404"
      ],
      "log_excerpts": []
    },
    "expected_cause": "registry_auth",
    "reference_rationale": "The same tag string as the missing-tag contrast is not evidence that it is missing; the observed response is unauthorized."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_auth",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_auth"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_access",
    "title": "Inspect registry access evidence",
    "description": "Review the registry's authentication response and the intended identity's repository permissions. Verify the workload's declared pull-secret association without sharing secret values."
  },
  "inference_ms": 0.010499992640689015,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry authentication or authorization failure. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 6

```json
{
  "id": "denied-scope",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "denied-scope",
    "group_id": "private-repository-access",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": "Failed",
          "message": "denied: requested access to the resource is denied; insufficient_scope: authorization failed"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_auth",
    "reference_rationale": "Explicit denial and insufficient scope indicate registry authorization failure."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_auth",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_auth"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_access",
    "title": "Inspect registry access evidence",
    "description": "Review the registry's authentication response and the intended identity's repository permissions. Verify the workload's declared pull-secret association without sharing secret values."
  },
  "inference_ms": 0.015166995581239462,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry authentication or authorization failure. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 7

```json
{
  "id": "missing-auth",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "missing-auth",
    "group_id": "missing-pull-identity",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "Head https://registry.example.test/v2/team/app/manifests/v2: no basic auth credentials",
          "image": null
        }
      ],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_auth",
    "reference_rationale": "Missing authentication credentials are explicitly reported."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_auth",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_auth"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_access",
    "title": "Inspect registry access evidence",
    "description": "Review the registry's authentication response and the intended identity's repository permissions. Verify the workload's declared pull-secret association without sharing secret values."
  },
  "inference_ms": 0.017708007362671196,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry authentication or authorization failure. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 8

```json
{
  "id": "forbidden",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "forbidden",
    "group_id": "forbidden-repository",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "Registry returned status code: 403 Forbidden for manifest request"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_auth",
    "reference_rationale": "A registry 403 response is an explicit access failure, not rate limiting."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_auth",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_auth"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_access",
    "title": "Inspect registry access evidence",
    "description": "Review the registry's authentication response and the intended identity's repository permissions. Verify the workload's declared pull-secret association without sharing secret values."
  },
  "inference_ms": 0.013208002201281488,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry authentication or authorization failure. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 9

```json
{
  "id": "io-timeout",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "io-timeout",
    "group_id": "registry-network-timeout",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "Get https://registry.example.test/v2/: dial tcp 192.0.2.5:443: i/o timeout"
        }
      ],
      "waiting": [
        {
          "reason": "ImagePullBackOff",
          "message": null,
          "image": null
        }
      ],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_connectivity",
    "reference_rationale": "A connection timeout to the registry identifies reachability failure."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_connectivity",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_connectivity"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_connectivity",
    "title": "Inspect registry connectivity evidence",
    "description": "Review DNS resolution and connection reachability evidence from the affected node's network, including proxy and firewall paths to the registry endpoint."
  },
  "inference_ms": 0.016582998796366155,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry DNS, network timeout, or connection refusal. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 10

```json
{
  "id": "connection-refused",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "connection-refused",
    "group_id": "registry-listener",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "dial tcp 192.0.2.9:5000: connect: connection refused",
          "image": null
        }
      ],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_connectivity",
    "reference_rationale": "Explicit refusal concerns the registry connection rather than repository permissions."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_connectivity",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_connectivity"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_connectivity",
    "title": "Inspect registry connectivity evidence",
    "description": "Review DNS resolution and connection reachability evidence from the affected node's network, including proxy and firewall paths to the registry endpoint."
  },
  "inference_ms": 0.01258301199413836,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry DNS, network timeout, or connection refusal. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 11

```json
{
  "id": "dns-failure",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "dns-failure",
    "group_id": "registry-dns",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "lookup registry.example.test on 192.0.2.53:53: no such host"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_connectivity",
    "reference_rationale": "The registry hostname cannot resolve."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_connectivity",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_connectivity"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_connectivity",
    "title": "Inspect registry connectivity evidence",
    "description": "Review DNS resolution and connection reachability evidence from the affected node's network, including proxy and firewall paths to the registry endpoint."
  },
  "inference_ms": 0.012208998668938875,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry DNS, network timeout, or connection refusal. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 12

```json
{
  "id": "deadline",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "deadline",
    "group_id": "registry-network-timeout",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "Pulling image registry.example.test/app:v3 failed: context deadline exceeded"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_connectivity",
    "reference_rationale": "The pull deadline is exceeded; this baseline groups that timeout with connectivity."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_connectivity",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_connectivity"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_connectivity",
    "title": "Inspect registry connectivity evidence",
    "description": "Review DNS resolution and connection reachability evidence from the affected node's network, including proxy and firewall paths to the registry endpoint."
  },
  "inference_ms": 0.01420799526385963,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry DNS, network timeout, or connection refusal. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 13

```json
{
  "id": "http-429",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "http-429",
    "group_id": "registry-quota",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "Registry returned HTTP 429 Too Many Requests; Retry-After: 60",
          "image": null
        }
      ],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_rate_limit",
    "reference_rationale": "429 and retry-after are explicit request-limit evidence."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_rate_limit",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_rate_limit"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_limits",
    "title": "Inspect rate-limit responses",
    "description": "Review the registry response status, rate-limit headers, retry-after value, and documented quota for the pulling identity."
  },
  "inference_ms": 0.012625008821487427,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry request or pull rate limiting, including HTTP 429. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 14

```json
{
  "id": "pull-quota",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "pull-quota",
    "group_id": "registry-quota",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "toomanyrequests: You have reached your pull rate limit"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_rate_limit",
    "reference_rationale": "The registry explicitly reports exhaustion of its pull quota."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_rate_limit",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_rate_limit"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_limits",
    "title": "Inspect rate-limit responses",
    "description": "Review the registry response status, rate-limit headers, retry-after value, and documented quota for the pulling identity."
  },
  "inference_ms": 0.01008401159197092,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry request or pull rate limiting, including HTTP 429. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 15

```json
{
  "id": "status-429",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "status-429",
    "group_id": "proxy-request-limit",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "Unexpected status code: 429 while reading registry manifest"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "registry_rate_limit",
    "reference_rationale": "An explicit HTTP status 429 on the registry request is a rate-limit signal."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_rate_limit",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_rate_limit"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_limits",
    "title": "Inspect rate-limit responses",
    "description": "Review the registry response status, rate-limit headers, retry-after value, and documented quota for the pulling identity."
  },
  "inference_ms": 0.010000003385357559,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry request or pull rate limiting, including HTTP 429. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 16

```json
{
  "id": "rate-limit-with-authenticated-identity",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "rate-limit-with-authenticated-identity",
    "group_id": "authenticated-quota",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "Registry pull rate limit exceeded for authenticated service identity"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": [
        "Token accepted; pull quota remaining: 0"
      ]
    },
    "expected_cause": "registry_rate_limit",
    "reference_rationale": "Authentication success does not prevent rate limiting; there is no explicit authentication failure."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "registry_rate_limit",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "specific_signal",
    "matched_causes": [
      "registry_rate_limit"
    ]
  },
  "recommended_check": {
    "id": "inspect_registry_limits",
    "title": "Inspect rate-limit responses",
    "description": "Review the registry response status, rate-limit headers, retry-after value, and documented quota for the pulling identity."
  },
  "inference_ms": 0.01820801116991788,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Registry request or pull rate limiting, including HTTP 429. Explicit category signals were detected by the evidence rules. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 17

```json
{
  "id": "backoff-only",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "backoff-only",
    "group_id": "incomplete-backoff",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [
        {
          "reason": "ImagePullBackOff",
          "message": null,
          "image": null
        }
      ],
      "images": [
        "registry.example.test/app:latest"
      ],
      "log_excerpts": []
    },
    "expected_cause": "other_or_insufficient_evidence",
    "reference_rationale": "Backoff is a retry state and supplies no precise root-cause evidence."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "other_or_insufficient_evidence",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "insufficient_evidence",
    "matched_causes": []
  },
  "recommended_check": {
    "id": "review_full_pull_evidence",
    "title": "Review the full pull failure",
    "description": "Collect the original pull error and correlate event time, image, container and node. Inspect evidence of causes outside these four categories before deciding."
  },
  "inference_ms": 0.004666988388635218,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Another image-pull cause, conflicting signals, or insufficient evidence. The evidence rules found no specific diagnostic signal. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 18

```json
{
  "id": "image-name-only",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "image-name-only",
    "group_id": "incomplete-image",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [],
      "images": [
        "registry.example.test/unauthorized:429"
      ],
      "log_excerpts": []
    },
    "expected_cause": "other_or_insufficient_evidence",
    "reference_rationale": "An image name containing diagnostic words or a numeric tag is not an error response."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "other_or_insufficient_evidence",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "insufficient_evidence",
    "matched_causes": []
  },
  "recommended_check": {
    "id": "review_full_pull_evidence",
    "title": "Review the full pull failure",
    "description": "Collect the original pull error and correlate event time, image, container and node. Inspect evidence of causes outside these four categories before deciding."
  },
  "inference_ms": 0.0019160070223733783,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Another image-pull cause, conflicting signals, or insufficient evidence. The evidence rules found no specific diagnostic signal. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 19

```json
{
  "id": "conflicting-manifest-and-auth",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "conflicting-manifest-and-auth",
    "group_id": "uncorrelated-errors",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "First event: manifest unknown"
        },
        {
          "reason": null,
          "message": "Second event: unauthorized: authentication required"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "other_or_insufficient_evidence",
    "reference_rationale": "Competing signals without container/time attribution cannot support one precise diagnosis."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "other_or_insufficient_evidence",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "conflicting_signals",
    "matched_causes": [
      "image_reference",
      "registry_auth"
    ]
  },
  "recommended_check": {
    "id": "review_full_pull_evidence",
    "title": "Review the full pull failure",
    "description": "Collect the original pull error and correlate event time, image, container and node. Inspect evidence of causes outside these four categories before deciding."
  },
  "inference_ms": 0.010709001799114048,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Another image-pull cause, conflicting signals, or insufficient evidence. The evidence rules found competing diagnostic signals. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 20

```json
{
  "id": "ambiguous-docker-denial",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "ambiguous-docker-denial",
    "group_id": "ambiguous-access-message",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "pull access denied for team/app, repository does not exist or may require 'docker login'",
          "image": null
        }
      ],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "other_or_insufficient_evidence",
    "reference_rationale": "The message itself offers both absence and access failure; neither should be forced as the sole cause."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "other_or_insufficient_evidence",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "conflicting_signals",
    "matched_causes": [
      "image_reference",
      "registry_auth"
    ]
  },
  "recommended_check": {
    "id": "review_full_pull_evidence",
    "title": "Review the full pull failure",
    "description": "Collect the original pull error and correlate event time, image, container and node. Inspect evidence of causes outside these four categories before deciding."
  },
  "inference_ms": 0.016542006051167846,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Another image-pull cause, conflicting signals, or insufficient evidence. The evidence rules found competing diagnostic signals. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 21

```json
{
  "id": "certificate-trust",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "certificate-trust",
    "group_id": "registry-tls-trust",
    "synthetic": true,
    "incident": {
      "events": [
        {
          "reason": null,
          "message": "Get https://registry.example.test/v2/: x509: certificate signed by unknown authority"
        }
      ],
      "waiting": [],
      "images": [],
      "log_excerpts": []
    },
    "expected_cause": "other_or_insufficient_evidence",
    "reference_rationale": "A certificate trust failure is a specific other cause, separate from missing evidence and from network reachability failure."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "other_or_insufficient_evidence",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "other_signal",
    "matched_causes": [
      "other_or_insufficient_evidence"
    ]
  },
  "recommended_check": {
    "id": "review_full_pull_evidence",
    "title": "Review the full pull failure",
    "description": "Collect the original pull error and correlate event time, image, container and node. Inspect evidence of causes outside these four categories before deciding."
  },
  "inference_ms": 0.014417004422284663,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Another image-pull cause, conflicting signals, or insufficient evidence. Explicit evidence points to a cause outside the four named categories. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```

## Case 22

```json
{
  "id": "disk-full",
  "status": "valid",
  "correct": true,
  "fixture": {
    "id": "disk-full",
    "group_id": "node-storage",
    "synthetic": true,
    "incident": {
      "events": [],
      "waiting": [
        {
          "reason": "ErrImagePull",
          "message": "failed to extract layer: no space left on device",
          "image": null
        }
      ],
      "images": [],
      "log_excerpts": [
        "Image unpack failed on local content store"
      ]
    },
    "expected_cause": "other_or_insufficient_evidence",
    "reference_rationale": "Local storage exhaustion is an explicit other cause, not uncertainty about an authentication error."
  },
  "error": null
}
```

### Prediction (including full raw response)

```json
{
  "provider": "rules",
  "execution_kind": "deterministic",
  "model": "image-pull-rules-v1",
  "model_revision": null,
  "runtime_version": "0.1.0",
  "dtype": null,
  "selected_cause": "other_or_insufficient_evidence",
  "probabilities": null,
  "ranked_options": null,
  "evidence_assessment": {
    "status": "other_signal",
    "matched_causes": [
      "other_or_insufficient_evidence"
    ]
  },
  "recommended_check": {
    "id": "review_full_pull_evidence",
    "title": "Review the full pull failure",
    "description": "Collect the original pull error and correlate event time, image, container and node. Inspect evidence of causes outside these four categories before deciding."
  },
  "inference_ms": 0.01812499249354005,
  "model_load_ms": 0.0,
  "review_status": "required",
  "review_reason": "Human review is required; model probabilities do not verify correctness.",
  "explanation_kind": "authored_template",
  "explanation": "Selected category: Another image-pull cause, conflicting signals, or insufficient evidence. Explicit evidence points to a cause outside the four named categories. This template is not model reasoning.",
  "usage": null,
  "raw_response": null
}
```
