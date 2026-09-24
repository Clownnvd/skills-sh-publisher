# Publishing workflow

Use this reference for an end-to-end publish, update, or diagnosis. Verify current CLI behavior with `npx skills --help` before copying commands.

## Repository layouts

For one skill, keep `SKILL.md` at repository root. For several skills, use `skills/<skill-name>/SKILL.md`. The CLI stops at a root skill unless current behavior or `--full-depth` says otherwise, so test the actual layout with `npx skills add <source> --list`.

The folder and frontmatter `name` use lowercase kebab-case and stay under 64 characters. The description is a routing contract: capability, trigger, and a useful exclusion when it prevents false activation.

Do not put essential agent instructions only in `README.md`. Skills load `SKILL.md`; the README serves people evaluating the repository.

## Build progressive resources

- Put shared decision logic and invariants in `SKILL.md`.
- Put conditional procedures and schemas in `references/`.
- Put repeated deterministic mechanics in `scripts/` and test them.
- Add `agents/openai.yaml` only for useful interface metadata. Its default prompt should mention `$skill-name`.
- Avoid empty directories, copied manuals, sample secrets, generated caches, and placeholders.

## Run local gates

```bash
python scripts/validate_skill_release.py . --strict
python -m unittest discover -s tests -v
npx skills add . --list
```

When the standard Codex validator exists, run it too:

```bash
python /path/to/skill-creator/scripts/quick_validate.py .
```

## Create and push the repository

```bash
git init -b main
git add .
git commit -m "feat: publish example skill"
gh repo create owner/repository --public --source . --remote origin --push
```

Before pushing, inspect `git status`, the staged diff, the remote, and secret-scanner output. Never force-push or replace an existing remote unless explicitly authorized.

Wait for CI and inspect the result:

```bash
gh run list --repo owner/repository --limit 5
gh run watch --repo owner/repository
```

## Test the public package

```bash
npx skills add owner/repository --list
npx skills add owner/repository --skill example-skill --agent codex -g -y --copy
```

The CLI may collect anonymous installation telemetry unless `DISABLE_TELEMETRY=1` is set. Publishing to the leaderboard requires an authorized tracked install. Do not silently override a user's telemetry choice.

## Verify skills.sh

The canonical skill page is `https://skills.sh/owner/repository/skill-name`.

The repository badge is:

```markdown
[![skills.sh](https://skills.sh/b/owner/repository)](https://skills.sh/owner/repository)
```

Run:

```bash
python scripts/verify_publication.py owner/repository example-skill --require-audits
```

The public audit endpoint may be available even when the catalog detail API requires Vercel OIDC:

```text
https://skills.sh/api/v1/skills/audit/owner/repository/skill-name
```

Treat HTTP 401 as an authentication boundary, not proof that a skill is absent. Public page, CLI install, and audit endpoint are independent checks.

## Tag a release

A release is recommended for changelogs and rollback points but is not required for indexing:

```bash
gh release create v1.0.0 --repo owner/repository \
  --title "Skill Name v1.0.0" \
  --notes "First public release."
```

Verify the tag targets the intended commit and the release state matches the request.

## Update an existing skill

1. Change the smallest necessary files.
2. Rerun local gates and clean-install discovery.
3. Commit and push to the default branch.
4. Wait for CI.
5. Run `npx skills update <skill>` or reinstall in a disposable environment.
6. Verify public page and audits after caches refresh.
7. Tag a semantic version when the change deserves a release boundary.

New installs fetch current repository contents. Existing installations need an update or reinstall.
