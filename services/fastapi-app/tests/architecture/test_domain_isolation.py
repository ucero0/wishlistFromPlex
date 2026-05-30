"""Guardrails: domain layer must not depend on outer layers."""
import ast
from pathlib import Path

DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "app" / "domain"

FORBIDDEN_PREFIXES = (
    "app.adapters",
    "app.infrastructure",
    "fastapi",
    "sqlalchemy",
    "httpx",
)


def _imports_in_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_domain_modules_do_not_import_adapters_or_infrastructure() -> None:
    violations: list[str] = []
    for path in DOMAIN_ROOT.rglob("*.py"):
        for imported in _imports_in_file(path):
            if any(
                imported == prefix or imported.startswith(f"{prefix}.")
                for prefix in FORBIDDEN_PREFIXES
            ):
                rel = path.relative_to(DOMAIN_ROOT.parent.parent)
                violations.append(f"{rel}: import {imported}")
    assert not violations, "Domain isolation violations:\n" + "\n".join(violations)
