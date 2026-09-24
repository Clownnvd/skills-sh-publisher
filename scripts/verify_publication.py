from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass


@dataclass
class Probe:
    name: str
    url: str
    status: int | None
    passed: bool
    detail: str


def build_urls(source: str, skill: str) -> dict[str, str]:
    normalized = source.strip().strip("/")
    if normalized.startswith("https://github.com/"):
        normalized = normalized.removeprefix("https://github.com/")
    parts = normalized.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("source must be owner/repository or a GitHub repository URL")
    owner, repository = parts
    catalog_source = f"{owner.lower()}/{repository.lower()}"
    return {
        "github": f"https://github.com/{owner}/{repository}",
        "skill": f"https://skills.sh/{catalog_source}/{skill}",
        "audit": f"https://skills.sh/api/v1/skills/audit/{catalog_source}/{skill}",
    }


def request(url: str) -> tuple[int | None, bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "skills-sh-publisher/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, response.read(), "ok"
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read() if exc.fp else b"", f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError) as exc:
        return None, b"", str(exc)


def probe_once(source: str, skill: str, require_audits: bool) -> list[Probe]:
    urls = build_urls(source, skill)
    probes: list[Probe] = []
    status, _, detail = request(urls["github"])
    probes.append(Probe("github_repository", urls["github"], status, status == 200, detail))

    status, body, detail = request(urls["skill"])
    page_ok = status == 200 and skill.lower() in body.decode("utf-8", errors="ignore").lower()
    probes.append(Probe("skills_sh_page", urls["skill"], status, page_ok, detail if page_ok else f"{detail}; skill name not confirmed"))

    status, body, detail = request(urls["audit"])
    audits: list[dict[str, object]] = []
    if status == 200:
        try:
            audits = json.loads(body.decode("utf-8")).get("audits", [])
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            detail = "audit response was not valid JSON"
    audit_ok = status == 200 and bool(audits)
    if not require_audits and status in {200, 404}:
        audit_ok = True
    verdicts = ", ".join(f"{item.get('provider')}: {item.get('status')}" for item in audits)
    probes.append(Probe("security_audits", urls["audit"], status, audit_ok, verdicts or detail))
    return probes


def verify(source: str, skill: str, attempts: int, delay: float, require_audits: bool) -> dict[str, object]:
    history: list[dict[str, object]] = []
    latest: list[Probe] = []
    for attempt in range(1, attempts + 1):
        latest = probe_once(source, skill, require_audits)
        history.append({"attempt": attempt, "probes": [asdict(item) for item in latest]})
        if all(item.passed for item in latest):
            break
        if attempt < attempts:
            time.sleep(delay)
    return {
        "published": bool(latest) and all(item.passed for item in latest),
        "source": source,
        "skill": skill,
        "attempts_used": len(history),
        "probes": [asdict(item) for item in latest],
        "history": history,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a GitHub Agent Skill and its skills.sh publication state.")
    parser.add_argument("source", help="owner/repository or GitHub repository URL")
    parser.add_argument("skill")
    parser.add_argument("--attempts", type=int, default=4)
    parser.add_argument("--delay", type=float, default=5.0)
    parser.add_argument("--require-audits", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.attempts <= 12:
        parser.error("--attempts must be between 1 and 12")
    if not 0 <= args.delay <= 30:
        parser.error("--delay must be between 0 and 30 seconds")
    try:
        payload = verify(args.source, args.skill, args.attempts, args.delay, args.require_audits)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["published"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
