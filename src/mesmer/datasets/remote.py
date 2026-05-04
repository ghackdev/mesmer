from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlparse

import httpx
from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.constants import (
    DATASET_ROW_INDEX_METADATA_KEY,
    DATASET_SOURCE_URL_METADATA_KEY,
    DATASET_TARGET_METADATA_KEY,
    DEFAULT_DATASET_CACHE_DIR,
)
from mesmer.core.enums import DatasetFormat
from mesmer.objectives.models import Objective
from mesmer.objectives.sources import ObjectiveSource


class DatasetColumnMap(MesmerModel):
    goal: str
    target: str | None = None
    metadata: list[str] = Field(default_factory=list)


class RemoteDatasetSource(ObjectiveSource):
    url: str
    format: DatasetFormat
    column_map: DatasetColumnMap
    cache_dir: Path = Path(DEFAULT_DATASET_CACHE_DIR)
    limit: int | None = None
    force_refresh: bool = False
    timeout_seconds: float = 30.0

    def __iter__(self) -> Iterator[Objective]:
        path = self.resolve_path()
        if self.format == DatasetFormat.CSV:
            yield from self._iter_csv(path)
            return
        if self.format == DatasetFormat.JSONL:
            yield from self._iter_jsonl(path)
            return
        raise ValueError(f"Unsupported dataset format: {self.format}")

    def resolve_path(self) -> Path:
        cache_path = self._cache_path()
        if cache_path.exists() and not self.force_refresh:
            return cache_path

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        parsed = urlparse(self.url)
        if parsed.scheme == "file":
            source_path = Path(parsed.path)
            shutil.copyfile(source_path, cache_path)
            return cache_path
        if parsed.scheme in {"http", "https"}:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = client.get(self.url)
                response.raise_for_status()
                cache_path.write_bytes(response.content)
            return cache_path
        raise ValueError(f"Unsupported dataset URL scheme: {parsed.scheme or '<empty>'}")

    def _iter_csv(self, path: Path) -> Iterator[Objective]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self._validate_columns(reader.fieldnames or [])
            for row_index, row in enumerate(reader):
                if self.limit is not None and row_index >= self.limit:
                    break
                yield self._objective_from_row(row, row_index)

    def _iter_jsonl(self, path: Path) -> Iterator[Objective]:
        with path.open("r", encoding="utf-8") as handle:
            for row_index, line in enumerate(handle):
                if self.limit is not None and row_index >= self.limit:
                    break
                if not line.strip():
                    continue
                row = json.loads(line)
                self._validate_columns(row.keys())
                yield self._objective_from_row(row, row_index)

    def _objective_from_row(self, row: dict[str, str], row_index: int) -> Objective:
        metadata = {
            column: row[column]
            for column in self.column_map.metadata
            if column in row
        }
        metadata[DATASET_SOURCE_URL_METADATA_KEY] = self.url
        metadata[DATASET_ROW_INDEX_METADATA_KEY] = row_index
        if self.column_map.target is not None:
            metadata[DATASET_TARGET_METADATA_KEY] = row[self.column_map.target]
        return Objective(goal=row[self.column_map.goal], metadata=metadata)

    def _validate_columns(self, columns: list[str] | tuple[str, ...] | object) -> None:
        available = list(columns)
        required = [self.column_map.goal]
        if self.column_map.target is not None:
            required.append(self.column_map.target)
        required.extend(self.column_map.metadata)
        missing = [column for column in required if column not in available]
        if missing:
            raise ValueError(
                "Dataset columns do not match column map. "
                f"missing={missing!r} available={available!r}"
            )

    def _cache_path(self) -> Path:
        digest = hashlib.sha256(self.url.encode("utf-8")).hexdigest()[:16]
        suffix = ".csv" if self.format == DatasetFormat.CSV else ".jsonl"
        return self.cache_dir / digest / f"dataset{suffix}"
