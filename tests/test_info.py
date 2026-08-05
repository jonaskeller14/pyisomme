import io
import unittest

from pyisomme import Info


class BaseInfoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_info = Info()
        # Notice duplicate key 'name' to test multi-dict capability
        self.populated_info = Info([("name", "Alice"), ("age", 30), ("name", "Bob")])


class TestGetItem(BaseInfoTestCase):
    def test_getitem_string_key_returns_first_match(self) -> None:
        self.assertEqual(self.populated_info["name"], "Alice")
        self.assertEqual(self.populated_info["age"], 30)

    def test_getitem_string_key_raises_keyerror_if_missing(self) -> None:
        with self.assertRaisesRegex(KeyError, "Key 'missing' not found."):
            _ = self.populated_info["missing"]

    def test_getitem_int_index_returns_tuple(self) -> None:
        self.assertEqual(self.populated_info[0], ("name", "Alice"))
        self.assertEqual(self.populated_info[2], ("name", "Bob"))

    def test_getitem_slice_returns_list_of_tuples(self) -> None:
        self.assertEqual(self.populated_info[:2], [("name", "Alice"), ("age", 30)])


class TestSetItem(BaseInfoTestCase):
    def test_setitem_string_appends_new_tuple(self) -> None:
        self.empty_info["city"] = "Karlsruhe"
        self.assertEqual(len(self.empty_info), 1)
        self.assertEqual(self.empty_info[0], ("city", "Karlsruhe"))

    def test_setitem_int_index_replaces_tuple(self) -> None:
        self.populated_info[1] = ("age", 31)
        self.assertEqual(self.populated_info[1], ("age", 31))
        self.assertEqual(len(self.populated_info), 3)

    def test_setitem_slice_replaces_elements(self) -> None:
        self.populated_info[0:2] = [("a", 1), ("b", 2)]
        self.assertEqual(self.populated_info[0], ("a", 1))
        self.assertEqual(self.populated_info[1], ("b", 2))


class TestGet(BaseInfoTestCase):
    def test_get_existing_key(self) -> None:
        self.assertEqual(self.populated_info.get("name"), "Alice")

    def test_get_missing_key_returns_default(self) -> None:
        self.assertIsNone(self.populated_info.get("missing"))
        self.assertEqual(self.populated_info.get("missing", "default_val"), "default_val")


class TestUpdate(BaseInfoTestCase):
    def test_update_from_dict_replaces_first_occurrence(self) -> None:
        self.populated_info.update({"name": "Charlie", "city": "Berlin"})

        # First 'name' updated, second 'name' preserved, 'city' appended
        expected = [
            ("name", "Charlie"),
            ("age", 30),
            ("name", "Bob"),
            ("city", "Berlin"),
        ]
        self.assertEqual(list(self.populated_info), expected)

    def test_update_from_list_of_tuples(self) -> None:
        self.populated_info.update([("age", 99), ("country", "DE")])
        self.assertEqual(self.populated_info.get("age"), 99)
        self.assertEqual(self.populated_info["country"], "DE")

    def test_update_returns_self_for_chaining(self) -> None:
        result = self.empty_info.update({"a": 1})
        self.assertIs(result, self.empty_info)


class TestAdd(BaseInfoTestCase):
    def test_add_from_dict_always_appends(self) -> None:
        self.populated_info.add({"name": "David"})

        # Should now have 3 'name' keys
        self.assertEqual(len(self.populated_info), 4)
        self.assertEqual(self.populated_info[3], ("name", "David"))

    def test_add_from_list_of_tuples(self) -> None:
        self.empty_info.add([("x", 10), ("y", 20)])
        self.assertEqual(len(self.empty_info), 2)
        self.assertEqual(self.empty_info["x"], 10)

    def test_add_returns_self(self) -> None:
        self.assertIs(self.empty_info.add({"a": 1}), self.empty_info)


class TestAccessors(BaseInfoTestCase):
    def test_keys(self) -> None:
        self.assertEqual(self.populated_info.keys(), ["name", "age", "name"])

    def test_values(self) -> None:
        self.assertEqual(self.populated_info.values(), ["Alice", 30, "Bob"])

    def test_items_returns_copy_of_list(self) -> None:
        items = self.populated_info.items()
        self.assertEqual(items, [("name", "Alice"), ("age", 30), ("name", "Bob")])
        self.assertIsNot(items, self.populated_info)  # Verify it's a new list object


class TestContains(BaseInfoTestCase):
    def test_contains_by_string_key(self) -> None:
        self.assertIn("name", self.populated_info)
        self.assertNotIn("missing", self.populated_info)

    def test_contains_by_tuple_item(self) -> None:
        self.assertIn(("name", "Alice"), self.populated_info)
        self.assertNotIn(("name", "Eve"), self.populated_info)


class TestWrite(unittest.TestCase):
    def test_write_formats_output_correctly(self) -> None:
        info = Info([("title", "Project"), ("empty_val", None)])
        buffer = io.StringIO()

        returned_buffer = info.write(buffer)

        self.assertIs(returned_buffer, buffer)
        output = buffer.getvalue()

        lines = output.strip().split("\n")
        self.assertEqual(len(lines), 2)
        # Verify 28-character left alignment and NOVALUE handling
        self.assertEqual(lines[0], "title                       :Project")
        self.assertEqual(lines[1], "empty_val                   :NOVALUE")


if __name__ == "__main__":
    unittest.main()
