from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace

import pytest

from pyisomme.limit import Limit


class TestLimit:
    def test_is_frozen_and_keeps_code_patterns_as_tuple(self) -> None:
        code_patterns = ("?1HEAD0000??ACR?",)
        limit = Limit(code_patterns, func=lambda x: x)

        assert limit.code_patterns is code_patterns
        with pytest.raises(FrozenInstanceError):
            limit.color = "green"  # type: ignore[misc]

    def test_equality_and_hash_use_identity(self) -> None:
        def func(x: float) -> float:
            return x

        first = Limit((), func=func)
        second = Limit((), func=func)

        assert first == first
        assert first != second
        assert len({first, second}) == 2

    def test_replace_returns_modified_copy(self) -> None:
        original = Limit((), func=lambda x: x, color="green", upper=True)

        modified = replace(original, color="red", upper=False, lower=True)

        assert modified is not original
        assert modified.color == "red"
        assert not modified.upper
        assert modified.lower
        assert original.color == "green"
        assert original.upper
        assert original.lower is None

    def test_decorated_subclass_defaults_and_replace(self) -> None:
        @dataclass(frozen=True, eq=False)
        class Limit_G(Limit):
            name: str | None = "Good"
            color: str = "green"
            rating: float = 4.0

        original = Limit_G((), func=lambda x: x)
        modified = replace(original, color="blue")

        assert original.name == "Good"
        assert original.color == "green"
        assert original.rating == 4.0
        assert isinstance(modified, Limit_G)
        assert modified.color == "blue"
