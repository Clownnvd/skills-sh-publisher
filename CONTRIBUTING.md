# Contributing

Keep changes focused on reliable Agent Skill packaging and skills.sh publication. Do not add provider-specific instructions without current source evidence.

Before opening a pull request, run:

```bash
python scripts/validate_skill_release.py . --strict
python -m unittest discover -s tests -v
npx skills add . --list
```

Update tests for deterministic behavior changes. Never commit credentials, private examples, generated caches, or browser data.
