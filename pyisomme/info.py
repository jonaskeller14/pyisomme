from __future__ import annotations

from typing import Any, IO


class Info(list):
    """Implements basic dictionary methods to a list-super-object. List allows duplicate keys."""
    def __setitem__(self, key, value):
        if isinstance(key, str):
            self.append((key, value))
        else:
            super().__setitem__(key, value)

    def __getitem__(self, key: Any):
        if isinstance(key, str):
            for name, value in self:
                if name == key:
                    return value
        else:
            return super().__getitem__(key)
        raise KeyError

    def get(self, key: str, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def update(self, other: list | dict) -> Info:
        """Replace if name already exists else append."""
        if isinstance(other, dict):
            return self.update([(n, v) for n, v in other.items()])

        for o_name, o_value in other:
            if o_name not in self:
                self[o_name] = o_value
            else:
                for idx, (name, value) in enumerate(self):
                    if name == o_name:
                        self[idx] = (o_name, o_value)
        return self

    def add(self, other: list | dict) -> Info:
        if isinstance(other, dict):
            other = [(name, value) for name, value in other.items()]
        super().extend(other)
        return self

    def keys(self) -> list:
        return [name for name, _ in self]

    def values(self) -> list:
        return [value for _, value in self]

    def items(self) -> list:
        return self

    def write(self, file: IO) -> IO:
        for name, value in self:
            file.write(f"{name.ljust(28, ' ')}:{value if value is not None else 'NOVALUE'}\n")
        return file

    def __contains__(self, key) -> bool:
        for name, _ in self:
            if name == key:
                return True
        return False
