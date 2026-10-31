# Issue tracker: GitHub

Issues, specs, and implementation tickets live in `MOTHblank/placecheck`.

Use the `gh` CLI with an explicit `--repo MOTHblank/placecheck` for issue operations. This clone also has an upstream remote, so do not rely on the CLI's inferred repository.

## Operations

- Verify access: `gh repo view MOTHblank/placecheck --json nameWithOwner,hasIssuesEnabled`.
- Publish a spec or ticket: `gh issue create --repo MOTHblank/placecheck --title "..." --body-file <path>`.
- Read: `gh issue view <number> --repo MOTHblank/placecheck --json number,title,body,labels,comments`.
- List: `gh issue list --repo MOTHblank/placecheck --state open --json number,title,body,labels`; filter with `--label` as needed.
- Comment: `gh issue comment <number> --repo MOTHblank/placecheck --body-file <path>`.
- Label: `gh issue edit <number> --repo MOTHblank/placecheck --add-label "..."` or `--remove-label "..."`.
- Close: post the explanation as a comment, then run `gh issue close <number> --repo MOTHblank/placecheck`. Comment separately even if the issue is already closed.

For multiline bodies, write the exact text to a temporary UTF-8 file and pass `--body-file`.

## Parents and blockers

Use GitHub native sub-issues and issue dependencies when supported by the installed CLI and repository. Check `gh issue create --help` and `gh issue edit --help` before using version-specific flags.

For API operations, target `repos/MOTHblank/placecheck/...` explicitly. GitHub dependency and sub-issue endpoints require issue database IDs, not issue numbers or node IDs.

If native links are unavailable, put `Part of #<parent>` and `Blocked by: #<blocker>, #<blocker>` at the top of the child body and maintain a child task list in the parent. A ticket is startable only when all blockers are closed.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Wayfinding

The map is one issue labelled `wayfinder:map`, with Notes, Decisions-so-far, and Fog sections. Link child tickets as sub-issues, or use the parent/task-list fallback above. Child labels are `wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, or `wayfinder:task`; create these labels when this workflow is first used.

Choose the first open child in map order with no open blockers or assignee. Claim it with `gh issue edit <number> --repo MOTHblank/placecheck --add-assignee @me`. Resolve it with an explanation comment, close it, and append the decision and issue link to the map.
