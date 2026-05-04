from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from pydantic import Field, PrivateAttr
from rich.console import Console, Group, RenderableType
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from mesmer.core.config import MesmerModel
from mesmer.core.enums import LogFormat

TEXT_FIELD_NAMES = frozenset(
    {"attacker_message", "goal", "message", "prompt", "reason", "response", "text"}
)
TEXT_PANEL_EVENTS = frozenset(
    {
        "objective.start",
        "conversation.start",
        "agent.plan",
        "transform.input",
        "transform.output",
        "target.call",
        "target.response",
        "judge.result",
        "run.error",
    }
)
SUCCESS_EVENTS = frozenset({"flow.stop", "run.finish"})
ERROR_EVENTS = frozenset({"run.error"})
CALL_EVENTS = frozenset({"target.call", "target.response", "judge.result"})
INDENT_START_EVENTS = frozenset(
    {"objective.start", "flow.start", "tree.depth.start", "agent.turn.start", "node.start"}
)
INDENT_STOP_EVENTS = frozenset(
    {"flow.stop", "tree.depth.finish", "agent.turn.finish", "node.finish", "run.finish"}
)
COMPACT_KEYS = ("attack", "target", "judges", "flow", "status", "succeeded", "attempts")
RUN_SUMMARY_KEYS = ("outcome", "execution_status", "succeeded", "attempts")


class RunLogger(MesmerModel):
    verbose: bool = False
    max_text_chars: int | None = 600
    log_format: LogFormat = LogFormat.RICH
    use_color: bool = True
    events: list[str] = Field(default_factory=list)
    started_at: float = Field(default_factory=perf_counter)
    indent: int = 0
    target_calls: int = 0
    judge_passes: int = 0
    judge_fails: int = 0
    total_latency_ms: float = 0.0
    max_candidates: int = 0

    _console: Console | None = PrivateAttr(default=None)

    def emit(self, event: str, **fields: Any) -> None:
        if not self.verbose:
            return
        self._observe(event, fields)
        self._adjust_indent_before(event)
        if self.log_format == LogFormat.COMPACT:
            line = self._compact_line(event, fields)
            self.events.append(line)
            print(line)
        else:
            line = self._plain_line(event, fields)
            self.events.append(line)
        if self.log_format == LogFormat.RICH and self._should_render(event) and self.use_color:
            self.console.print(self._render(event, fields))
        elif self.log_format == LogFormat.RICH and self._should_render(event):
            print(line)
        self._adjust_indent_after(event)

    @property
    def console(self) -> Console:
        if self._console is None:
            self._console = Console(highlight=False)
        return self._console

    def text(self, value: str | None) -> str:
        if value is None:
            return ""
        collapsed = value.replace("\n", "\\n")
        if self.max_text_chars is None:
            return collapsed
        if len(collapsed) <= self.max_text_chars:
            return collapsed
        return collapsed[: self.max_text_chars] + "...[truncated]"

    def _plain_line(self, event: str, fields: dict[str, Any]) -> str:
        clean_fields = {
            key: self._format_plain_value(value)
            for key, value in fields.items()
            if value is not None
        }
        suffix = ""
        if clean_fields:
            suffix = " " + " ".join(f"{key}={value}" for key, value in clean_fields.items())
        return f"[mesmer] {event}{suffix}"

    def _compact_line(self, event: str, fields: dict[str, Any]) -> str:
        payload = {
            "t": self._elapsed(),
            "level": self.indent,
            "event": event,
        }
        payload.update(
            {
                key: self._compact_value(value)
                for key, value in fields.items()
                if value is not None
            }
        )
        return json.dumps(payload, separators=(",", ":"), default=str)

    def _compact_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, float):
            return round(value, 2)
        if isinstance(value, list):
            return [self._compact_value(item) for item in value]
        if isinstance(value, tuple):
            return [self._compact_value(item) for item in value]
        if isinstance(value, set):
            return [self._compact_value(item) for item in sorted(value, key=str)]
        if isinstance(value, dict):
            return {
                str(key): self._compact_value(item)
                for key, item in value.items()
            }
        return value

    def _should_render(self, event: str) -> bool:
        return event not in {"transform.input", "transform.output"}

    def _observe(self, event: str, fields: dict[str, Any]) -> None:
        if event == "target.call":
            self.target_calls += 1
        if event == "target.response":
            self.total_latency_ms += float(fields.get("latency_ms") or 0)
        if event == "judge.result":
            if fields.get("status") == "pass":
                self.judge_passes += 1
            else:
                self.judge_fails += 1
        if "candidates" in fields and fields["candidates"] is not None:
            self.max_candidates = max(self.max_candidates, int(fields["candidates"]))

    def _render(self, event: str, fields: dict[str, Any]) -> RenderableType:
        if event == "run.start":
            return self._run_header(fields)
        if event == "run.finish":
            return self._run_footer(fields)

        event_row = self._event_row(event, fields)
        detail_table = self._detail_table(event, fields)
        if detail_table is None or event not in TEXT_PANEL_EVENTS:
            if detail_table is None:
                return event_row
            return Group(event_row, Padding(detail_table, (0, 0, 0, self._panel_indent())))
        return Padding(
            Panel(
                Group(event_row, Rule(style="dim"), detail_table),
                border_style=self._event_style(event),
                padding=(0, 1),
                expand=False,
            ),
            (0, 0, 0, self._panel_indent()),
        )

    def _run_header(self, fields: dict[str, Any]) -> RenderableType:
        title = Text()
        title.append("MESMER", style="bold magenta")
        title.append(" run", style="bold white")
        title.append("  run.start", style="dim")
        title.append("  ")
        title.append(str(fields.get("run_id", "")), style="dim")

        table = Table.grid(padding=(0, 2))
        table.add_column(style="dim", no_wrap=True)
        table.add_column()
        for key in COMPACT_KEYS:
            if key in fields:
                table.add_row(key, self._value_text(key, fields[key]))

        return Panel(
            Group(title, Rule(style="magenta"), table),
            border_style="magenta",
            padding=(0, 1),
            expand=False,
        )

    def _run_footer(self, fields: dict[str, Any]) -> RenderableType:
        outcome = fields.get("outcome", fields.get("status", "unknown"))
        succeeded = bool(fields.get("succeeded"))
        style = "green" if succeeded else "red"

        title = Text()
        title.append("RUN COMPLETE", style=f"bold {style}")
        title.append(f"  {self._elapsed()}", style="dim")
        title.append("  run.finish", style="dim")

        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="dim", no_wrap=True)
        summary.add_column()
        for key in RUN_SUMMARY_KEYS:
            if key in fields:
                summary.add_row(key, self._value_text(key, fields[key]))
        summary.add_row("target_calls", self._value_text("target_calls", self.target_calls))
        summary.add_row("judge_pass", self._value_text("status", self.judge_passes))
        summary.add_row("judge_fail", self._value_text("status", self.judge_fails))
        summary.add_row("latency_sum", self._value_text("latency_ms", self.total_latency_ms))
        if self.max_candidates:
            summary.add_row("max_candidates", self._value_text("candidates", self.max_candidates))

        scoreboard = self._scoreboard(outcome, succeeded)
        return Panel(
            Group(title, Rule(style=style), scoreboard, summary),
            border_style=style,
            padding=(0, 1),
            expand=False,
        )

    def _scoreboard(self, outcome: Any, succeeded: bool) -> Table:
        table = Table.grid(padding=(0, 1))
        table.add_column(no_wrap=True)
        table.add_column(no_wrap=True)
        table.add_column(no_wrap=True)
        table.add_column(no_wrap=True)
        table.add_row(
            self._pill("outcome", str(outcome), "green" if succeeded else "red"),
            self._pill("calls", str(self.target_calls), "cyan"),
            self._pill("pass", str(self.judge_passes), "green"),
            self._pill("fail", str(self.judge_fails), "red" if self.judge_fails else "dim"),
        )
        return table

    def _pill(self, label: str, value: str, style: str) -> Text:
        text = Text()
        text.append(f"{label} ", style="dim")
        text.append(value, style=f"bold {style}")
        return text

    def _event_row(self, event: str, fields: dict[str, Any]) -> Table:
        table = Table.grid(padding=(0, 1))
        table.add_column(no_wrap=True)
        table.add_column(no_wrap=True)
        table.add_column(no_wrap=True)
        table.add_column()
        table.add_row(
            self._branch_text(event),
            Text(self._elapsed(), style="dim"),
            Text(event, style=f"bold {self._event_style(event)}"),
            self._inline_fields(fields),
        )
        return table

    def _branch_text(self, event: str) -> Text:
        text = Text()
        if self.indent:
            text.append("   " * self.indent, style="dim")
        text.append(self._event_icon(event), style=f"bold {self._event_style(event)}")
        return text

    def _inline_fields(self, fields: dict[str, Any]) -> Text:
        text = Text()
        first = True
        for key, value in fields.items():
            if value is None or key in TEXT_FIELD_NAMES or key.endswith("_id"):
                continue
            if not first:
                text.append("  ", style="dim")
            first = False
            text.append(key, style="dim")
            text.append("=")
            text.append_text(self._value_text(key, value))
        return text

    def _detail_table(self, event: str, fields: dict[str, Any]) -> Table | None:
        if event == "attacker.seed":
            return None
        rows = [
            (key, self.text(str(value)))
            for key, value in fields.items()
            if value is not None and key in TEXT_FIELD_NAMES
        ]
        if not rows:
            return None
        table = Table.grid(padding=(0, 1))
        table.add_column(style="dim", no_wrap=True)
        table.add_column(ratio=1)
        for key, value in rows:
            table.add_row(key, Text(value, style="white", overflow="fold"))
        return table

    def _value_text(self, key: str, value: Any) -> Text:
        return Text(self._format_display_value(value), style=self._field_style(key, value))

    def _format_display_value(self, value: Any) -> str:
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    def _format_plain_value(self, value: Any) -> str:
        if isinstance(value, str):
            return repr(self.text(value))
        if isinstance(value, float):
            return f"{value:.2f}"
        return repr(value)

    def _elapsed(self) -> str:
        elapsed = perf_counter() - self.started_at
        if elapsed < 1:
            return f"+{elapsed * 1000:.0f}ms"
        return f"+{elapsed:.2f}s"

    def _panel_indent(self) -> int:
        return self.indent * 3

    def _adjust_indent_before(self, event: str) -> None:
        if event in INDENT_STOP_EVENTS:
            self.indent = max(0, self.indent - 1)

    def _adjust_indent_after(self, event: str) -> None:
        if event in INDENT_START_EVENTS:
            self.indent += 1
        if event == "flow.stop":
            self.indent = max(0, self.indent - 1)

    def _event_icon(self, event: str) -> str:
        if event in ERROR_EVENTS:
            return "x"
        if event in CALL_EVENTS:
            return ">"
        if event.endswith(".start"):
            return "▶"
        if event.endswith(".finish"):
            return "✓"
        if event == "flow.stop":
            return "■"
        return "•"

    def _event_style(self, event: str) -> str:
        if event in ERROR_EVENTS:
            return "red"
        if event in SUCCESS_EVENTS:
            return "green"
        if event.startswith("target."):
            return "cyan"
        if event.startswith("judge."):
            return "yellow"
        if (
            event.startswith("attacker.")
            or event.startswith("transform.")
            or event.startswith("tree.")
            or event.startswith("agent.")
            or event.startswith("node.")
        ):
            return "blue"
        if event.startswith("objective."):
            return "magenta"
        return "white"

    def _field_style(self, key: str, value: Any) -> str:
        if key == "status" and value in {"pass", "succeeded"}:
            return "green"
        if key == "status" and value in {"fail", "failed"}:
            return "red"
        if key == "outcome":
            return "green" if value == "objective_succeeded" else "red"
        if key == "execution_status":
            return "green" if value == "succeeded" else "red"
        if key == "succeeded":
            return "green" if value else "red"
        if key in {
            "score",
            "attempts",
            "candidates",
            "turn",
            "depth",
            "latency_ms",
            "target_calls",
        }:
            return "cyan"
        if key.endswith("_id") or key in {"run_id", "candidate_id", "response_id"}:
            return "dim"
        return "white"


NULL_LOGGER = RunLogger(verbose=False)
