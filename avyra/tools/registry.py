"""Metadata-only registry. V1 has no execution or AI tool dispatch."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    permissions: tuple[str, ...]
    requires_confirmation: bool = True

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.name) or not self.description.strip():
            raise ValueError("Tool requires a valid name and description.")
        if not isinstance(self.permissions, tuple) or not self.permissions or any(not isinstance(p, str) or not p.strip() for p in self.permissions):
            raise ValueError("Tool permissions must be an explicit nonempty tuple.")
        if type(self.requires_confirmation) is not bool:
            raise ValueError("Confirmation policy must be boolean.")


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError("Tool is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        return self._tools[name]

    def list_tools(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._tools.values())
