"""Configuration model for user-editable settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Configuration:
    """User-editable settings loaded from config/settings.toml."""

    output_path: str = "~/Desktop"
    repos_file: str = "config/repos.txt"

    @property
    def resolved_output_path(self) -> Path:
        return Path(self.output_path).expanduser()

    @property
    def resolved_repos_file(self) -> Path:
        return Path(self.repos_file).expanduser()
