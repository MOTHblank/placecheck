# Placecheck

## Existing project instructions

The Portuguese instructions in `DEVELOPMENT_PLAN.md` and `LOCAL_SESSION_PROMPT.md` remain binding. This file summarizes their ongoing rules in English; consult the originals for detailed requirements and acceptance criteria. Plugin workflows supplement these project instructions.

## Session workflow

1. Read `DEVELOPMENT_PLAN.md` in full and `LOCAL_SESSION_PROMPT.md` before changing any file.
2. Check `git status`, inspect the repository structure and existing implementation, and identify the current sprint. Use `README.md` for local setup and reported progress, then verify that progress against the code and acceptance criteria.
3. Present a short implementation plan before making changes.
4. Complete the current sprint's acceptance criteria before advancing to the next sprint. The Sprint 0 task in the initial-session prompt applies to bootstrap; on continuing sessions, resume from the verified current state.
5. Run the available tests relevant to the change. Validate `docker compose up` for bootstrap and changes affecting the running stack; report any checks that could not be completed.
6. Update `README.md` when setup, usage, or progress changes. Report what changed, validation results, and real remaining work.

## Product and implementation rules

- Build the real estate aggregation MVP defined in `DEVELOPMENT_PLAN.md`: collect permitted listings, normalize them, group duplicate offers for the same property, preserve price history, support search and comparison, and redirect users to the original listing. Contact and transactions happen on the source site.
- Keep the modular Django monolith and the stack defined in the plan. Do not introduce microservices or features listed as outside the MVP. Explain and justify architecture changes before implementing them.
- Keep providers separate from domain logic. Providers and crawlers must never save directly to `Listing`; use `Provider -> RawListing -> Normalizer -> NormalizedListing -> upsert Listing`.
- Use asynchronous ingestion through Celery. Preserve idempotent updates, price-change history, last-seen tracking, and listing inactivation according to the plan.
- Keep initial deduplication rule-based with configurable scoring and candidate filtering rather than comparing every property. Machine learning and mandatory AI dependencies are outside the MVP.
- Prefer simple, explicit code. Add dependencies only when necessary, keep migrations small and reviewable, and create tests alongside important domain rules.

## Sources and crawlers

Before implementing or changing a source integration, follow the crawler policies in section 11 of `DEVELOPMENT_PLAN.md` and the source's storage permissions.

- Collect only from authorized or permitted sources. Respect Terms of Use, check `robots.txt`, identify the crawler where applicable, and use rate limits and caching to avoid unnecessary requests.
- Do not bypass CAPTCHA, login, or access blocks, rotate IPs to evade protections, or access private endpoints.
- Preserve original URLs, support source removal, and reflect listing deletions and inactivation. Minimize personal data; collect phone numbers or email addresses only when necessary and with an appropriate basis.

## Agent skills

Use the installed `mattpocock-skills` plugin. This repository stores its configuration below; skill files remain managed by the plugin.

### Issue tracker

Track issues, specs, and tickets in GitHub Issues for `MOTHblank/placecheck`. Read `docs/agents/issue-tracker.md` before tracker operations.

### Triage labels

Use the five default triage roles. Read `docs/agents/triage-labels.md` before triaging or applying workflow labels.

### Domain docs

Use a single root `GLOSSARY.md` and `docs/adr/`. Read `docs/agents/domain.md` before exploring domain concepts or architecture.
