"""Guardrails: composition must not import HTTP factories."""
import ast
from pathlib import Path

COMPOSITION_ROOT = Path(__file__).resolve().parents[2] / "app" / "composition"

FORBIDDEN_PREFIXES = (
    "app.factories",
    "app.infrastructure.persistence.active_downloads.repo",
    "app.infrastructure.persistence.antivirus.repo",
    "app.infrastructure.persistence.blacklist_torrent.repo",
    "app.infrastructure.persistence.deferred_downloads.repo",
    "app.infrastructure.persistence.plex.repo",
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


def test_composition_modules_do_not_import_factories_or_repos_directly() -> None:
    violations: list[str] = []
    for path in COMPOSITION_ROOT.rglob("*.py"):
        if path.name == "persistence.py":
            continue
        for imported in _imports_in_file(path):
            if any(
                imported == prefix or imported.startswith(f"{prefix}.")
                for prefix in FORBIDDEN_PREFIXES
            ):
                rel = path.relative_to(COMPOSITION_ROOT.parent.parent)
                violations.append(f"{rel}: import {imported}")
    assert not violations, (
        "Composition should use persistence/external builders:\n" + "\n".join(violations)
    )
