# Security policy for the demo

This repository is a synthetic portfolio demonstration, not banking software.

- Never enter real identity, account, card, authentication, or financial data.
- Never add real bank credentials or vendor API collections.
- Use AWS profiles or workload roles; do not place AWS keys in `.env`.
- The default local mode makes no external calls and cannot move money.
- Any future write-like capability must remain behind deterministic validation, idempotency, and explicit human approval.
- Public deployment requires real user authentication, server-side rate limiting, private telemetry, and an infrastructure/IAM review.

Report a security concern privately to the repository owner. Do not include secrets or real customer data in an issue.

