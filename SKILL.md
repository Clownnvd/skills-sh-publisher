---
name: skills-sh-publisher
description: Package, publish, update, and verify Agent Skills in public GitHub repositories and on skills.sh. Use when creating a release-ready skill repository, listing a skill through the skills CLI, diagnosing why a skill is missing from skills.sh, or checking publication and security-audit status; skip ordinary skill authoring that will remain local.
metadata:
  version: "1.0.0"
---

# Skills.sh Publisher

Ship an Agent Skill from a local folder to a verified public listing. Treat GitHub publication, CLI telemetry, releases, catalog indexing, and security audits as separate observable states.

## Preserve authority

- Creating local skill files is not permission to create a public repository, push commits, create a release, or emit install telemetry.
- Perform each external mutation only when the current request authorizes it. Never publish secrets, credentials, private examples, browser state, or proprietary context.
- Keep the user's repository, license, visibility, author identity, and versioning choices unless a missing decision blocks publication.

## Choose the mode

- **Package:** build or harden the local skill and repository without publishing.
- **Publish:** validate, create or update the public GitHub repository, trigger catalog discovery, and verify the listing.
- **Update:** ship a revision, refresh installations, and verify the public snapshot.
- **Diagnose:** inspect repository, CLI discovery, skills.sh, caching, and audits without changing external state.

Inspect the current `npx skills --help` and official skills.sh documentation before acting because flags, indexing, APIs, and caching can change.

## Publication workflow

1. Confirm the skill has one discoverable capability, a kebab-case name, and a description that says what it does and when it applies.
2. Read [references/release-gates.md](references/release-gates.md) and apply every required preflight gate.
3. For exact commands and layouts, read [references/publishing-workflow.md](references/publishing-workflow.md).
4. For lessons from a real release, indexing, badge repair, and audit verification, read [references/field-notes.md](references/field-notes.md).
5. Run the deterministic package check:

   ```bash
   python scripts/validate_skill_release.py /path/to/skill --strict
   ```

6. Test discovery locally and from the public source:

   ```bash
   npx skills add /path/to/repository --list
   npx skills add owner/repository --list
   ```

7. Publish only after validation passes. Prefer a public GitHub repository, clean CI, an explicit license, and a human-facing README. A GitHub release is recommended for version history but does not list the skill on skills.sh.
8. Trigger discovery with an authorized CLI installation that leaves anonymous telemetry enabled:

   ```bash
   npx skills add owner/repository --skill skill-name -g -y
   ```

   There is no separate leaderboard submission form. Catalog visibility follows tracked CLI installation and may be delayed by caches and audit processing.
9. Verify rather than trusting the install command:

   ```bash
   python scripts/verify_publication.py owner/repository skill-name --require-audits
   ```

10. Report repository, installability, skills.sh listing, release, and audits separately. A pass in one state does not imply the others passed.

## Quality rules

- `SKILL.md` must be exact-case and contain valid `name` and `description` frontmatter.
- Keep shared agent instructions concise; route conditional detail into `references/` and repeated mechanics into tested `scripts/`.
- A repository README is for humans. Do not assume an agent loads it as skill instructions.
- Use the canonical badge form `[![skills.sh](https://skills.sh/b/owner/repo)](https://skills.sh/owner/repo)`.
- Test a clean install path, not only the development checkout.
- Treat audit warnings as evidence to review, not decorations to hide.
- Bound indexing retries. Default to four checks with short waits, then report the exact unresolved state.
- Never fabricate install counts, audit results, catalog URLs, or release success.

## Recovery

- If local validation fails, repair the smallest failing artifact and rerun the failed gate plus package regression tests.
- If CLI discovery fails, inspect filename casing, frontmatter, repository depth, default branch, and `--full-depth` behavior before retrying.
- If installation succeeds but the page is absent, confirm telemetry was not disabled, wait through the documented cache window, and retry within the declared budget.
- If the listing is stale, verify the default-branch commit, perform a clean update or reinstall, and compare the public snapshot after cache expiry.
- If an audit warns or fails, inspect the provider report and remove the risky behavior. Do not repeatedly reinstall to bury the result.

## Completion evidence

Finish only when the requested states have direct evidence: validation output, clean-install output, repository URL and commit, skills.sh URL, release URL when requested, and current audit verdicts when available. Report cache delays or authenticated API boundaries as unresolved instead of claiming success.
