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


class SubDummyClass(DummyClass):
    @property
    def sub_property(self):
        return "sub_value"


def test_get_property_fields_with_inheritance():
    """Test get_property_fields when passing a class with inheritance."""
    properties = _FileAttributesCore.get_property_fields(SubDummyClass)
    assert set(properties) == {"property_field", "another_property", "sub_property"}


def test_get_property_fields_with_cached_property():
    """Test get_property_fields uses _cached_property_fields if available."""

    class DummyWithCache:
        _cached_property_fields = ("prop1", "prop2")

    instance = DummyWithCache()
    properties = _FileAttributesCore.get_property_fields(instance)
    assert properties == ("prop1", "prop2")


def test_core_cached_property_fields():
    """Test _cached_property_fields on _FileAttributesCore instance."""
    from pathlib import Path

    class DummyCore(_FileAttributesCore):
        @property
        def dummy_prop(self):
            return True

    instance = DummyCore(Path("dummy"))

    # _cached_property_fields should be populated
    props = instance._cached_property_fields
    assert "dummy_prop" in props

    # get_property_fields should use the cache
    assert _FileAttributesCore.get_property_fields(instance) == props
