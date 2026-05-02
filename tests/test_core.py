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
    """Test get_property_fields with a subclass to check MRO iteration."""
    properties = _FileAttributesCore.get_property_fields(SubDummyClass)
    assert set(properties) == {"property_field", "another_property", "sub_property"}


def test_get_property_fields_with_cached_property():
    """Test get_property_fields uses _cached_property_fields if available."""

    class CachedPropsClass:
        def __init__(self):
            self._cached_property_fields = ("cached_prop1", "cached_prop2")

        @property
        def actual_prop(self):
            return "actual_value"

    instance = CachedPropsClass()
    properties = _FileAttributesCore.get_property_fields(instance)
    # Because it has _cached_property_fields, it should return that directly
    assert set(properties) == {"cached_prop1", "cached_prop2"}


def test_core_cached_property_fields(tmp_path):
    """Test the actual _cached_property_fields implementation on _FileAttributesCore."""
    dummy_file = tmp_path / "dummy.txt"
    dummy_file.touch()

    # Create a subclass to test _cached_property_fields
    class MyAttributes(_FileAttributesCore):
        @property
        def my_prop(self):
            return "value"

    instance = MyAttributes(dummy_file)
    # This should evaluate the cached property
    properties = instance._cached_property_fields

    assert "my_prop" in properties

    # Check that get_property_fields uses the cache for this instance
    assert _FileAttributesCore.get_property_fields(instance) == properties
