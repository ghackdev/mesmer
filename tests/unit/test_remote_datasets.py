from __future__ import annotations

from mesmer import DatasetColumnMap, DatasetFormat, ObjectiveSource, RemoteDatasetSource


def test_remote_csv_dataset_loads_and_caches_objectives(tmp_path) -> None:
    source_file = tmp_path / "source.csv"
    cache_dir = tmp_path / "cache"
    source_file.write_text(
        "goal,target,category\n"
        "make marker,MARKER_READY,smoke\n"
        "make other,OTHER_READY,smoke\n",
        encoding="utf-8",
    )
    source = RemoteDatasetSource(
        url=source_file.as_uri(),
        format=DatasetFormat.CSV,
        column_map=DatasetColumnMap(
            goal="goal",
            target="target",
            metadata=["category"],
        ),
        cache_dir=cache_dir,
        limit=1,
    )

    objectives = list(source)

    assert len(objectives) == 1
    assert objectives[0].goal == "make marker"
    assert objectives[0].metadata["target"] == "MARKER_READY"
    assert objectives[0].metadata["category"] == "smoke"
    assert source.resolve_path().exists()


def test_objective_source_remote_uses_dataset_format_enum(tmp_path) -> None:
    source_file = tmp_path / "source.jsonl"
    source_file.write_text('{"goal":"make marker","target":"MARKER_READY"}\n', encoding="utf-8")

    source = ObjectiveSource.remote(
        url=source_file.as_uri(),
        format=DatasetFormat.JSONL,
        column_map=DatasetColumnMap(goal="goal", target="target"),
        cache_dir=tmp_path / "cache",
        limit=1,
    )

    objectives = list(source)

    assert objectives[0].goal == "make marker"
    assert objectives[0].metadata["target"] == "MARKER_READY"


def test_remote_dataset_missing_columns_show_available_columns(tmp_path) -> None:
    source_file = tmp_path / "source.csv"
    source_file.write_text("goal\nmake marker\n", encoding="utf-8")
    source = RemoteDatasetSource(
        url=source_file.as_uri(),
        format=DatasetFormat.CSV,
        column_map=DatasetColumnMap(goal="goal", target="target"),
        cache_dir=tmp_path / "cache",
    )

    try:
        list(source)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected missing column validation error.")

    assert "missing=['target']" in message
    assert "available=['goal']" in message
