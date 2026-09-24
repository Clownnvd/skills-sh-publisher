# Field notes from a real publication

These notes capture reusable evidence from publishing `Clownnvd/task-mitosis` on 24 September 2026. They are operational lessons, not timeless platform guarantees; recheck current documentation and CLI help.

## What produced the listing

1. A public GitHub repository exposed a valid root `SKILL.md` on the default branch.
2. CI validated the package and deterministic helper tests.
3. A real `npx skills add Clownnvd/task-mitosis` installation emitted anonymous telemetry.
4. The skill appeared at `https://skills.sh/clownnvd/task-mitosis/task-mitosis` without a submission form.
5. Security providers audited it automatically after discovery.

Pushing to GitHub makes the source installable; a tracked CLI install makes skills.sh aware of it.

## Repairs worth preserving

The working badge source is repository-level: `https://skills.sh/b/clownnvd/task-mitosis`. The individual skill page adds the skill slug. Mixing those URL shapes produced a broken badge and required a follow-up commit.

The `v1.0.0` release documented a stable artifact and rollback point, but indexing did not depend on the GitHub release. Security audits appeared asynchronously after discovery.

The catalog detail endpoint returned HTTP 401 without Vercel OIDC while the audit endpoint remained publicly readable. Verification therefore needs independent probes and must not equate API authentication failure with publication failure.

A repository can look correct locally while omitting a file from Git or breaking on a clean machine. The reliable order is local validation, clean CI, public `--list`, clean install, public page, then audits.

## Recorded evidence

- Repository: `https://github.com/Clownnvd/task-mitosis`
- Release: `https://github.com/Clownnvd/task-mitosis/releases/tag/v1.0.0`
- skills.sh: `https://skills.sh/clownnvd/task-mitosis/task-mitosis`
- CI: successful initial publish and canonical badge repair runs
- Audits observed: Gen Agent Trust Hub pass, Socket pass, Snyk pass

Never copy these verdicts to another skill. Verify every skill's current audits.
