from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{24,}\b"),
    "OpenAI-style token": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".svg"}
MAX_FILE_BYTES = 2 * 1024 * 1024


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must begin with YAML frontmatter delimited by ---")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is missing its closing --- delimiter")
    fields: dict[str, str] = {}
    lines = text[4:end].splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line or line.startswith((" ", "\t", "#")) or ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if value in {">", "|", ">-", "|-"}:
            block: list[str] = []
            index += 1
            while index < len(lines) and (not lines[index] or lines[index].startswith((" ", "\t"))):
                block.append(lines[index].strip())
                index += 1
            fields[key] = " ".join(part for part in block if part)
            continue
        fields[key] = strip_quotes(value)
        index += 1
    return fields, text[end + 5 :]


def local_targets(skill_file: Path, text: str) -> list[Path]:
    targets: list[Path] = []
    for raw in LINK_RE.findall(text):
        target = raw.strip().split(" ", 1)[0].strip("<>")
        if not target or target.startswith(("http://", "https://", "mailto:", "#", "data:")):
            continue
        target = unquote(target.split("#", 1)[0])
        targets.append((skill_file.parent / target).resolve())
    return targets


def validate(skill_dir: Path, expected_name: str | None, strict: bool) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    facts: dict[str, object] = {"path": str(skill_dir.resolve())}
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return {"valid": False, "errors": ["Missing exact-case SKILL.md"], "warnings": [], "facts": facts}

    text = skill_file.read_text(encoding="utf-8")
    try:
        frontmatter, body = parse_frontmatter(text)
    except ValueError as exc:
        errors.append(str(exc))
        frontmatter, body = {}, ""

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    expected = expected_name or skill_dir.resolve().name
    facts.update({"name": name, "description_length": len(description)})

    if not name:
        errors.append("Frontmatter is missing name")
    elif not NAME_RE.fullmatch(name):
        errors.append("Skill name must be lowercase kebab-case")
    elif len(name) > 64:
        errors.append("Skill name exceeds 64 characters")
    if name and name != expected:
        errors.append(f"Skill name {name!r} does not match expected name {expected!r}")
    if not description:
        errors.append("Frontmatter is missing description")
    elif len(description) > 1024:
        errors.append("Description exceeds 1,024 characters")
    elif "<" in description or ">" in description:
        errors.append("Description must not contain angle brackets")
    if re.search(r"\b(?:TODO|TBD|FIXME)\b|\[TODO", text, re.IGNORECASE):
        errors.append("SKILL.md contains an unfinished placeholder")
    if len(body.strip()) < 80:
        warnings.append("SKILL.md body is unusually short")
    for target in local_targets(skill_file, text):
        if not target.exists():
            errors.append(f"Broken local link from SKILL.md: {target}")

    files = [path for path in skill_dir.rglob("*") if path.is_file() and ".git" not in path.parts]
    facts["file_count"] = len(files)
    for path in files:
        relative = path.relative_to(skill_dir)
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            errors.append(f"File exceeds 2 MB: {relative}")
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            errors.append(f"Private environment file must not be published: {relative}")
        if path.suffix.lower() not in TEXT_SUFFIXES or size > 512_000:
            continue
        try:
            contents = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(contents):
                errors.append(f"Possible {label} in {relative}")

    agent_file = skill_dir / "agents" / "openai.yaml"
    if agent_file.is_file():
        agent_text = agent_file.read_text(encoding="utf-8")
        for required in ("display_name:", "short_description:", "default_prompt:"):
            if required not in agent_text:
                warnings.append(f"agents/openai.yaml is missing {required[:-1]}")
        if name and f"${name}" not in agent_text:
            errors.append(f"agents/openai.yaml default prompt must mention ${name}")

    readme = skill_dir / "README.md"
    if not readme.is_file():
        warnings.append("Repository README.md is missing")
    else:
        readme_text = readme.read_text(encoding="utf-8")
        if "npx skills add" not in readme_text:
            warnings.append("README.md has no npx skills install command")
        if "skills.sh/b/" not in readme_text:
            warnings.append("README.md has no canonical skills.sh badge")
    for recommended in ("LICENSE", "SECURITY.md", "CONTRIBUTING.md", ".github/workflows/ci.yml"):
        if not (skill_dir / recommended).is_file():
            warnings.append(f"Recommended release file is missing: {recommended}")

    valid = not errors and (not strict or not warnings)
    return {"valid": valid, "errors": errors, "warnings": warnings, "facts": facts, "strict": strict}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Agent Skill before a public skills.sh release.")
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--expected-name")
    parser.add_argument("--strict", action="store_true", help="Treat release-hygiene warnings as failures")
    args = parser.parse_args()
    if not args.skill_dir.is_dir():
        payload = {"valid": False, "errors": [f"Not a directory: {args.skill_dir}"], "warnings": [], "facts": {}}
    else:
        payload = validate(args.skill_dir, args.expected_name, args.strict)
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
