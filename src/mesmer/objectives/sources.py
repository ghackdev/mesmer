from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from mesmer.core.config import MesmerModel
from mesmer.core.enums import DatasetFormat
from mesmer.objectives.models import Objective

if TYPE_CHECKING:
    from mesmer.datasets.remote import DatasetColumnMap, RemoteDatasetSource


class ObjectiveSource(MesmerModel, ABC):
    @abstractmethod
    def __iter__(self) -> Iterator[Objective]:
        raise NotImplementedError

    @classmethod
    def single(cls, objective: str | Objective) -> SingleObjectiveSource:
        return SingleObjectiveSource(objective=Objective.coerce(objective))

    @classmethod
    def list(cls, objectives: Iterable[str | Objective]) -> ListObjectiveSource:
        return ListObjectiveSource(objectives=[Objective.coerce(item) for item in objectives])

    @classmethod
    def jsonl(cls, path: str | Path) -> JsonlObjectiveSource:
        return JsonlObjectiveSource(path=Path(path))

    @classmethod
    def csv(cls, path: str | Path, goal_column: str = "goal") -> CsvObjectiveSource:
        return CsvObjectiveSource(path=Path(path), goal_column=goal_column)

    @classmethod
    def remote(
        cls,
        url: str,
        format: DatasetFormat,
        column_map: DatasetColumnMap,
        cache_dir: str | Path | None = None,
        limit: int | None = None,
    ) -> RemoteDatasetSource:
        from mesmer.datasets.remote import RemoteDatasetSource

        data = {
            "url": url,
            "format": format,
            "column_map": column_map,
            "limit": limit,
        }
        if cache_dir is not None:
            data["cache_dir"] = Path(cache_dir)
        return RemoteDatasetSource(
            **data,
        )


class SingleObjectiveSource(ObjectiveSource):
    objective: Objective

    def __iter__(self) -> Iterator[Objective]:
        yield self.objective


class ListObjectiveSource(ObjectiveSource):
    objectives: list[Objective]

    def __iter__(self) -> Iterator[Objective]:
        yield from self.objectives


class JsonlObjectiveSource(ObjectiveSource):
    path: Path

    def __iter__(self) -> Iterator[Objective]:
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    payload = json.loads(line)
                    yield Objective(**payload)


class CsvObjectiveSource(ObjectiveSource):
    path: Path
    goal_column: str = "goal"

    def __iter__(self) -> Iterator[Objective]:
        with self.path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                yield Objective(goal=row[self.goal_column], metadata=dict(row))
