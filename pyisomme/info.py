from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import IO, Any


class Info(list[tuple[str, Any]]):
    """
    Implements basic dictionary methods for a list-like object while preserving key ordering.

    Supports duplicate keys, which is common in ISO-MME data files that often contain
    multiple 'Comments' keys or repeated metadata entries.
    """

    def __setitem__(self, key: str | int | slice, value: Any) -> None:  # type: ignore[override]
        if isinstance(key, str):
            self.append((key, value))
        else:
            super().__setitem__(key, value)

    def __getitem__(self, key: str | int | slice) -> Any:  # type: ignore[override]
        if isinstance(key, str):
            for name, value in self:
                if name == key:
                    return value
            raise KeyError(f"Key '{key}' not found.")
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def update(self, other: Mapping[str, Any] | Iterable[tuple[str, Any]]) -> Info:
        """Replace the FIRST occurrence of a key if it exists, else append."""
        iterable = other.items() if isinstance(other, Mapping) else other

        for o_name, o_value in iterable:
            # Single pass replacement
            for idx, (name, _) in enumerate(self):
                if name == o_name:
                    self[idx] = (o_name, o_value)
                    break
            else:
                # The for-else block executes if no 'break' was hit
                self.append((o_name, o_value))  # pyright: ignore[reportArgumentType]

        return self

    def add(self, other: Mapping[str, Any] | Iterable[tuple[str, Any]]) -> Info:
        iterable = other.items() if isinstance(other, Mapping) else other
        super().extend(iterable)  # pyright: ignore[reportArgumentType]
        return self

    def keys(self) -> list[str]:
        return [name for name, _ in self]

    def values(self) -> list[Any]:
        return [value for _, value in self]

    def items(self) -> list[tuple[str, Any]]:
        # Returning a copy prevents accidental mutation of the underlying list
        return list(self)

    def write(self, file: IO[str]) -> IO[str]:
        for name, value in self:
            val_str = value if value is not None else "NOVALUE"
            file.write(f"{name:<28}:{val_str}\n")
        return file

    def __contains__(self, key: Any) -> bool:
        if isinstance(key, str):
            return any(name == key for name, _ in self)
        # Fall back to standard list item checking for tuples
        return super().__contains__(key)

    def __repr__(self) -> str:
        return "\n".join(
            [
                f"{name:<28}:{value if value is not None else 'NOVALUE'}"
                for name, value in self.items()
            ]
        )
