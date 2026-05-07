"""Guarded local coding tools for repository exploration."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GuardrailError(Exception):
    """Raised when a coding tool request violates local safety rules."""


@dataclass(frozen=True)
class CommandResult:
    """Result from a guarded local command."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class Workspace:
    """A bounded filesystem view for local coding-agent tools."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"Workspace does not exist: {self.root}")
        if not self.root.is_dir():
            raise NotADirectoryError(f"Workspace is not a directory: {self.root}")

    def resolve(self, relative_path: str = ".") -> Path:
        path = (self.root / relative_path).resolve()
        if path != self.root and self.root not in path.parents:
            raise GuardrailError(f"Path escapes workspace: {relative_path}")
        return path

    def list_files(self, *, max_files: int = 200) -> list[Path]:
        files: list[Path] = []
        for path in sorted(self.root.rglob("*")):
            if _should_skip(path):
                continue
            if path.is_file():
                files.append(path.relative_to(self.root))
            if len(files) >= max_files:
                break
        return files

    def read_file(self, relative_path: str, *, max_chars: int = 20_000) -> str:
        path = self.resolve(relative_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]

    def search_text(self, query: str, *, max_matches: int = 50) -> list[str]:
        matches: list[str] = []
        for relative in self.list_files(max_files=2_000):
            path = self.resolve(str(relative))
            try:
                for line_number, line in enumerate(
                    path.read_text(encoding="utf-8", errors="replace").splitlines(),
                    start=1,
                ):
                    if query.lower() in line.lower():
                        matches.append(f"{relative}:{line_number}: {line.strip()}")
                    if len(matches) >= max_matches:
                        return matches
            except OSError:
                continue
        return matches

    def run_command(self, command: list[str], *, timeout_seconds: float = 30.0) -> CommandResult:
        if not command:
            raise GuardrailError("Command cannot be empty")
        _validate_command(command)
        completed = subprocess.run(
            command,
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return CommandResult(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


def _should_skip(path: Path) -> bool:
    ignored_parts = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
        "dist",
        "build",
    }
    return any(part in ignored_parts for part in path.parts)


def _validate_command(command: list[str]) -> None:
    executable = command[0]
    allowed = {
        "git",
        "pytest",
        "ruff",
        "uv",
        "ls",
        "pwd",
        "find",
    }
    if executable not in allowed:
        raise GuardrailError(f"Command is not allowlisted: {executable}")

    joined = " ".join(command)
    blocked_fragments = [
        " rm ",
        "rm -",
        "reset --hard",
        "checkout --",
        "clean -fd",
        "push",
        "curl",
        "wget",
    ]
    if any(fragment in f" {joined} " for fragment in blocked_fragments):
        raise GuardrailError(f"Command is blocked by guardrails: {joined}")
