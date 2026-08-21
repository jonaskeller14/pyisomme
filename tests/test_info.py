import io

import pytest

from pyisomme import Info


@pytest.fixture
def empty_info() -> Info:
    """Provides a fresh, empty Info instance for a test."""
    return Info()


@pytest.fixture
def populated_info() -> Info:
    """Provides a populated Info instance for a test."""
    # Notice duplicate key 'name'
    return Info([("name", "Alice"), ("age", 30), ("name", "Bob")])


class TestGetItem:
    def test_getitem_string_key_returns_first_match(self, populated_info: Info) -> None:
        assert populated_info["name"] == "Alice"
        assert populated_info["age"] == 30

    def test_getitem_string_key_raises_keyerror_if_missing(
        self, populated_info: Info
    ) -> None:
        with pytest.raises(KeyError, match="Key 'missing' not found."):
            _ = populated_info["missing"]

    def test_getitem_int_index_returns_tuple(self, populated_info: Info) -> None:
        assert populated_info[0] == ("name", "Alice")
        assert populated_info[2] == ("name", "Bob")

    def test_getitem_slice_returns_list_of_tuples(self, populated_info: Info) -> None:
        assert populated_info[:2] == [("name", "Alice"), ("age", 30)]


class TestSetItem:
    def test_setitem_string_appends_new_tuple(self, empty_info: Info) -> None:
        empty_info["city"] = "Karlsruhe"
        assert len(empty_info) == 1
        assert empty_info[0] == ("city", "Karlsruhe")

    def test_setitem_int_index_replaces_tuple(self, populated_info: Info) -> None:
        populated_info[1] = ("age", 31)
        assert populated_info[1] == ("age", 31)
        assert len(populated_info) == 3

    def test_setitem_slice_replaces_elements(self, populated_info: Info) -> None:
        populated_info[0:2] = [("a", 1), ("b", 2)]
        assert populated_info[0] == ("a", 1)
        assert populated_info[1] == ("b", 2)


class TestGet:
    def test_get_existing_key(self, populated_info: Info) -> None:
        assert populated_info.get("name") == "Alice"

    def test_get_missing_key_returns_default(self, populated_info: Info) -> None:
        assert populated_info.get("missing") is None
        assert populated_info.get("missing", "default_val") == "default_val"


class TestUpdate:
    def test_update_from_dict_replaces_first_occurrence(
        self, populated_info: Info
    ) -> None:
        populated_info.update({"name": "Charlie", "city": "Berlin"})

        # First 'name' updated, second 'name' preserved, 'city' appended
        expected = [
            ("name", "Charlie"),
            ("age", 30),
            ("name", "Bob"),
            ("city", "Berlin"),
        ]
        assert list(populated_info) == expected

    def test_update_from_list_of_tuples(self, populated_info: Info) -> None:
        populated_info.update([("age", 99), ("country", "DE")])
        assert populated_info.get("age") == 99
        assert populated_info["country"] == "DE"

    def test_update_returns_self_for_chaining(self, empty_info: Info) -> None:
        result = empty_info.update({"a": 1})
        assert result is empty_info


class TestAdd:
    def test_add_from_dict_always_appends(self, populated_info: Info) -> None:
        populated_info.add({"name": "David"})

        # Should now have 3 'name' keys
        assert len(populated_info) == 4
        assert populated_info[3] == ("name", "David")

    def test_add_from_list_of_tuples(self, empty_info: Info) -> None:
        empty_info.add([("x", 10), ("y", 20)])
        assert len(empty_info) == 2
        assert empty_info["x"] == 10

    def test_add_returns_self(self, empty_info: Info) -> None:
        assert empty_info.add({"a": 1}) is empty_info


class TestAccessors:
    def test_keys(self, populated_info: Info) -> None:
        assert populated_info.keys() == ["name", "age", "name"]

    def test_values(self, populated_info: Info) -> None:
        assert populated_info.values() == ["Alice", 30, "Bob"]

    def test_items_returns_copy_of_list(self, populated_info: Info) -> None:
        items = populated_info.items()
        assert items == [("name", "Alice"), ("age", 30), ("name", "Bob")]
        assert items is not populated_info  # Verify it's a new list object


class TestContains:
    def test_contains_by_string_key(self, populated_info: Info) -> None:
        assert "name" in populated_info
        assert "missing" not in populated_info

    def test_contains_by_tuple_item(self, populated_info: Info) -> None:
        assert ("name", "Alice") in populated_info
        assert ("name", "Eve") not in populated_info


class TestWrite:
    def test_write_formats_output_correctly(self) -> None:
        info = Info([("title", "Project"), ("empty_val", None)])
        buffer = io.StringIO()

        returned_buffer = info.write(buffer)

        assert returned_buffer is buffer
        output = buffer.getvalue()

        lines = output.strip().split("\n")
        assert len(lines) == 2
        # Verify 28-character left alignment and NOVALUE handling
        assert lines[0] == "title                       :Project"
        assert lines[1] == "empty_val                   :NOVALUE"
