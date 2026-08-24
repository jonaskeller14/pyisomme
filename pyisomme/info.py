from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import IO, TypeVar, Union, cast, overload

InfoValue = Union[str, int, float, bool, datetime, None]
InfoItem = tuple[str, InfoValue]
DefaultValue = TypeVar("DefaultValue")
InfoInput = Union[Mapping[str, InfoValue], Iterable[InfoItem]]


def format_value(value: InfoValue) -> str:
    """Serialize one parsed metadata value to its ISO-MME text representation."""
    if value is None:
        return "NOVALUE"
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@dataclass(init=False)
class Info:
    """Ordered ISO-MME metadata which preserves repeated descriptor names.

    String keys address the first matching descriptor; :meth:`get_all` exposes
    every value stored for repeatable descriptor names such as ``Comments``.
    """

    _items: list[InfoItem] = field(default_factory=list)

    def __init__(
        self, items: Mapping[str, InfoValue] | Iterable[InfoItem] = ()
    ) -> None:
        if isinstance(items, Mapping):
            mapping = cast(Mapping[str, InfoValue], items)
            self._items = list(mapping.items())
        else:
            self._items = list(items)

    def __iter__(self) -> Iterator[InfoItem]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __add__(self, other: Mapping[str, InfoValue] | Iterable[InfoItem]) -> Info:
        result = Info(self)
        return result.add(other)

    @overload
    def __getitem__(self, key: str) -> InfoValue: ...

    @overload
    def __getitem__(self, key: int) -> InfoItem: ...

    @overload
    def __getitem__(self, key: slice) -> list[InfoItem]: ...

    def __getitem__(
        self, key: str | int | slice
    ) -> InfoValue | InfoItem | list[InfoItem]:
        if isinstance(key, str):
            for name, value in self._items:
                if name == key:
                    return value
            raise KeyError(f"Key '{key}' not found.")
        return self._items[key]

    @overload
    def __setitem__(self, key: str, value: InfoValue) -> None: ...

    @overload
    def __setitem__(self, key: int, value: InfoItem) -> None: ...

    @overload
    def __setitem__(self, key: slice, value: Iterable[InfoItem]) -> None: ...

    def __setitem__(
        self,
        key: str | int | slice,
        value: InfoValue | InfoItem | Iterable[InfoItem],
    ) -> None:
        if isinstance(key, str):
            self._items.append((key, cast(InfoValue, value)))
        elif isinstance(key, int):
            self._items[key] = cast(InfoItem, value)
        else:
            self._items[key] = cast(Iterable[InfoItem], value)

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return any(name == item for name, _ in self._items)
        return item in self._items

    def __repr__(self) -> str:
        return "\n".join(
            f"{name:<28}:{format_value(value)}" for name, value in self._items
        )

    @overload
    def get(self, key: str) -> InfoValue: ...

    @overload
    def get(self, key: str, default: DefaultValue) -> InfoValue | DefaultValue: ...

    def get(
        self, key: str, default: DefaultValue | None = None
    ) -> InfoValue | DefaultValue | None:
        return next((value for name, value in self._items if name == key), default)

    def get_all(self, key: str) -> list[InfoValue]:
        """Return every value stored under ``key``, in file order."""
        return [value for name, value in self._items if name == key]

    def update(self, other: Mapping[str, InfoValue] | Iterable[InfoItem]) -> Info:
        """Replace the first occurrence of each key, or append it if absent."""
        entries = other.items() if isinstance(other, Mapping) else other
        for other_name, other_value in cast(Iterable[InfoItem], entries):
            for index, (name, _) in enumerate(self._items):
                if name == other_name:
                    self._items[index] = (other_name, other_value)
                    break
            else:
                self._items.append((other_name, other_value))
        return self

    def add(self, other: Mapping[str, InfoValue] | Iterable[InfoItem]) -> Info:
        """Append metadata entries, including entries with existing keys."""
        entries = other.items() if isinstance(other, Mapping) else other
        self._items.extend(cast(Iterable[InfoItem], entries))
        return self

    def remove(self, item: InfoItem) -> None:
        self._items.remove(item)

    def keys(self) -> list[str]:
        return [name for name, _ in self._items]

    def values(self) -> list[InfoValue]:
        return [value for _, value in self._items]

    def items(self) -> list[InfoItem]:
        """Return a copy so callers cannot mutate the internal item list."""
        return list(self._items)

    def write(self, file: IO[str]) -> IO[str]:
        for name, value in self._items:
            file.write(f"{name:<28}:{format_value(value)}\n")
        return file
