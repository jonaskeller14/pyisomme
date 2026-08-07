from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
import unittest

from pyisomme.limit import Limit


class TestLimit(unittest.TestCase):
    def test_is_frozen_and_keeps_code_patterns_as_tuple(self) -> None:
        code_patterns = ("?1HEAD0000??ACR?",)
        limit = Limit(code_patterns, func=lambda x: x)

        self.assertIs(limit.code_patterns, code_patterns)
        with self.assertRaises(FrozenInstanceError):
            limit.color = "green"  # type: ignore[misc]

    def test_equality_and_hash_use_identity(self) -> None:
        def func(x: float) -> float:
            return x

        first = Limit((), func=func)
        second = Limit((), func=func)

        self.assertEqual(first, first)
        self.assertNotEqual(first, second)
        self.assertEqual(len({first, second}), 2)

    def test_replace_returns_modified_copy(self) -> None:
        original = Limit((), func=lambda x: x, color="green", upper=True)

        modified = replace(original, color="red", upper=False, lower=True)

        self.assertIsNot(modified, original)
        self.assertEqual(modified.color, "red")
        self.assertFalse(modified.upper)
        self.assertTrue(modified.lower)
        self.assertEqual(original.color, "green")
        self.assertTrue(original.upper)
        self.assertIsNone(original.lower)

    def test_decorated_subclass_defaults_and_replace(self) -> None:
        @dataclass(frozen=True, eq=False)
        class Limit_G(Limit):
            name: str | None = "Good"
            color: str = "green"
            rating: float = 4.0

        original = Limit_G((), func=lambda x: x)
        modified = replace(original, color="blue")

        self.assertEqual(original.name, "Good")
        self.assertEqual(original.color, "green")
        self.assertEqual(original.rating, 4.0)
        self.assertIsInstance(modified, Limit_G)
        self.assertEqual(modified.color, "blue")


if __name__ == "__main__":
    unittest.main()
