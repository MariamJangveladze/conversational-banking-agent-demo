# Architecture decisions

## ADR-001 — Clean derivative, not a literal fork

The portfolio demo keeps the source project's conversational-banking idea and AWS Strands learning value, but does not copy vendor credentials, API collections, branding, mandatory onboarding logic, or customer-like records.

## ADR-002 — The model proposes; code authorizes

The optional Bedrock path classifies intent only. A deterministic workflow owns supported operations, limits, state transitions, and approval. The model receives no direct banking tools.

## ADR-003 — Mock-first runtime

`DEMO_MODE=mock` is the default, so the repository is runnable without AWS credentials or cloud cost. `DEMO_MODE=bedrock` is an explicit opt-in for demonstrating a Strands classifier.

## ADR-004 — Synthetic data and simulation language

All identities, accounts, merchants, balances, and actions are fictional. The UI says “preview,” “approve simulation,” and “no money moved” instead of claiming successful banking operations.

## ADR-005 — Minimal observability

Telemetry stores operation, latency, model label, token counts, estimated cost, and outcome. It intentionally excludes prompts, message bodies, and identity data.

