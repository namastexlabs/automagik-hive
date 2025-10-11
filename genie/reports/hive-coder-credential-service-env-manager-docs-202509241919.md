# Death Testament – Env Manager Docs (hive-coder)

## Scope & Outcomes
- Documented the `EnvFileManager` split across `lib/auth/CREDENTIAL_INTEGRATION.md`, covering responsibilities, constructor injection, and migration guidance.
- Updated onboarding guidance in `README.md` so newcomers learn to rely on the CLI + manager pairing for credential flows.
- Refreshed wish plan (`genie/wishes/credential-service-env-split-wish.md`) and forge report (`genie/reports/forge-plan-credential-service-env-split-202509241752.md`) with final architecture summary plus Death Testament links.

## Validation & Evidence
- Documentation-only change; no automated linting required. Spot-checked rendered Markdown locally.

## Files Touched
- `lib/auth/CREDENTIAL_INTEGRATION.md`
- `README.md`
- `genie/wishes/credential-service-env-split-wish.md`
- `genie/reports/forge-plan-credential-service-env-split-202509241752.md`
- `genie/reports/hive-coder-credential-service-env-manager-docs-202509241919.md`

## Risks & Follow-ups
- Future Docker manager decisions still outstanding per `hive-tests-env-manager-tests-202509241911.md`; documentation now points back to that guidance for product review.
- Recommend human review to confirm onboarding language strikes the right balance between automation guidance and manual flexibility.

