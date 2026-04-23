from __future__ import annotations

from pathlib import Path

import yaml

from routex_gateway.core.config import AppSettings
from routex_gateway.domain.models import ProjectConfig


class ProjectConfigService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def load_for_project(
        self, project_id: str, project_config_path: str | None = None
    ) -> ProjectConfig | None:
        candidate_paths: list[Path] = []
        if project_config_path:
            candidate_paths.append(Path(project_config_path))
        candidate_paths.append(self._settings.project_configs_dir / project_id / "project.yaml")
        candidate_paths.append(self._settings.project_configs_dir / "examples" / "project.yaml")

        for path in candidate_paths:
            if not path.exists():
                continue
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return ProjectConfig.model_validate(payload)
        return None
