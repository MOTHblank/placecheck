# Domain docs

## Before exploring

Read root `GLOSSARY.md`, when present, and the ADRs in `docs/adr/` relevant to the area being changed.

Placecheck uses a single domain context across `backend/` and `frontend/`. Store shared terminology in root `GLOSSARY.md` and architecture decisions in `docs/adr/`.

When those files do not exist, proceed silently. The `domain-modeling` skill creates them as terms and decisions are resolved; setup does not scaffold empty domain documents.

## Vocabulary and decisions

Use glossary terms consistently in issue titles, code, tests, and explanations. If a needed concept is missing, reconsider the terminology or raise the gap during domain modeling.

Identify conflicts with existing ADRs explicitly and explain why a decision should be reopened.
