# Test Strategy

## Unit tests

The test suite validates:

- input validation;
- deterministic generation;
- exact forward transform reprojection;
- inverse transform stability;
- edge-brightening activation;
- nominal DRAM/FinFET hybrid localization;
- rotation and scale recovery;
- NCC-vs-hybrid failure recovery;
- failure categorization;
- polygon IoU.

Result: **14/14 tests passed**.

## Integration tests

`evaluate_manifest.py` was exercised on a generated image pair and successfully produced a prediction CSV.

## System tests

`infer.py` was exercised from the command line on an independently written PNG pair and returned structured prediction output with method, confidence and runtime.

## UAT-style checks

The externally visible workflow is:

```text
reference.png + search.png
        ↓
python infer.py ...
        ↓
(x, y) + score + runtime
```

No database or network service is required by the inference path.

## Failure/negative cases

The implementation explicitly handles:

- missing files;
- undecodable files;
- empty/tiny images;
- non-grayscale arrays;
- non-finite arrays;
- unsupported dimensions;
- invalid method names;
- no feature descriptors;
- insufficient feature matches;
- RANSAC failure;
- implausible transforms;
- no candidate proposals.
