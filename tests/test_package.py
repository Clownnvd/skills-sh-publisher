from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skill_release.py"
VERIFIER = ROOT / "scripts" / "verify_publication.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseValidatorTests(unittest.TestCase):
    def run_validator(self, target: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(VALIDATOR), str(target), *extra], capture_output=True, text=True, encoding="utf-8", check=False)

    def test_repository_passes_strict_validation(self) -> None:
        result = self.run_validator(ROOT, "--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_relative_dot_path_uses_resolved_folder_name(self) -> None:
        result = subprocess.run([sys.executable, str(VALIDATOR), ".", "--strict"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_minimal_valid_fixture_passes(self) -> None:
        result = self.run_validator(ROOT / "tests" / "fixtures" / "valid-skill")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_fixture_is_rejected(self) -> None:
        result = self.run_validator(ROOT / "tests" / "fixtures" / "invalid-skill")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["valid"])


class PublicationVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module(VERIFIER, "verify_publication")

    def test_build_urls_accepts_slug(self) -> None:
        urls = self.module.build_urls("Clownnvd/task-mitosis", "task-mitosis")
        self.assertEqual(urls["skill"], "https://skills.sh/clownnvd/task-mitosis/task-mitosis")
        self.assertEqual(urls["github"], "https://github.com/Clownnvd/task-mitosis")

    def test_build_urls_rejects_invalid_source(self) -> None:
        with self.assertRaises(ValueError):
            self.module.build_urls("only-one-part", "example")


if __name__ == "__main__":
    unittest.main()
