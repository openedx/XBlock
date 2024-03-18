"""Tests of the xblock.internal module."""
from unittest import TestCase

from xblock.internal import class_lazy


class TestLazyClassProperty(TestCase):
    """
    Tests of @class_lazy.
    """
    class Base:
        """Test class that uses @class_lazy."""
        @class_lazy
        def isolated_dict(cls):  # pylint: disable=no-self-argument
            "Return a different dict for each subclass."
            return {}

    class Derived(Base):
        """Test class that inherits a @class_lazy definition."""

    def test_isolation(self):
        self.assertEqual({}, self.Base.isolated_dict)
        self.assertEqual({}, self.Derived.isolated_dict)
        self.assertIsNot(self.Base.isolated_dict, self.Derived.isolated_dict)
