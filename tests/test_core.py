import tempfile
from pathlib import Path

from file_attributes import FileAttributes
from file_attributes._core import _FileAttributesCore


class DummyClass:
    def __init__(self):
        self.regular_attribute = "value"

    @property
    def property_field(self):
        return "property_value"

    @property
    def another_property(self):
        return "another_value"

    def regular_method(self):
        pass


def test_get_property_fields_with_class():
    """Test get_property_fields when passing a class."""
    properties = _FileAttributesCore.get_property_fields(DummyClass)
    assert set(properties) == {"property_field", "another_property"}


def test_get_property_fields_with_instance():
    """Test get_property_fields when passing an instance of a class."""
    dummy_instance = DummyClass()
    properties = _FileAttributesCore.get_property_fields(dummy_instance)
    assert set(properties) == {"property_field", "another_property"}


def test_get_property_fields_no_properties():
    """Test get_property_fields with a class that has no properties."""

    class NoPropsClass:
        def __init__(self):
            self.attr = 1

        def method(self):
            pass

    properties = _FileAttributesCore.get_property_fields(NoPropsClass)
    assert properties == ()

    instance = NoPropsClass()
    properties_instance = _FileAttributesCore.get_property_fields(instance)
    assert properties_instance == ()


def test_file_attributes_repr_and_str():
    """Test __repr__ and __str__ magic methods of FileAttributes to bump coverage."""

    with tempfile.NamedTemporaryFile() as tmp:
        attrs = FileAttributes(Path(tmp.name))

        # Test __repr__
        rep = repr(attrs)
        assert "FileAttributes" in rep

        # Test __str__
        s = str(attrs)
        assert "File: " in s
        assert "Attribute" in s
