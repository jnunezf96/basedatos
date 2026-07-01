# Source Cleanup Review Report

Generated from `resources/source_cleanup_review_pack.tsv`.

Use this report to decide the remaining per-token cases. To apply a decision, edit the TSV columns `decision` and `replacement`, then run `python3 resources/apply_source_cleanup_review_pack_decisions.py --apply`.

Allowed decisions:

- `pending`: no-op; still needs review.
- `keep`: intentional apparatus; no-op.
- `accept_bracket`: replace `[token]` with `token`, unless `replacement` is filled.
- `replace`: replace `review_token` with `replacement`.
- `ignore` or `disallow`: no-op.

## Summary

- Review rows: 0
- By decision: 
- By triage: 

## Source Groups
