"""
Tests for the ``xblock_i18n`` template tag library.
"""
from unittest import TestCase

from django.apps import apps
from django.template import Context, Template
from django.utils import translation
from django.utils.translation import trans_real

from xblock.test.utils.test_resources import MockI18nService
from xblock.utils.templatetags.i18n import I18N_SERVICE_CONTEXT_KEY


class FakePluralI18nService:
    """
    An i18n service with one plural string, in the shape ``BlockFirstTranslation`` reads.
    """
    _catalog = {
        ("%(n)s apple", 0): "%(n)s manzana",
        ("%(n)s apple", 1): "%(n)s manzanas",
    }

    def gettext(self, message):
        return self._catalog.get(message, message)

    def ngettext(self, singular, plural, n):
        return self._catalog.get((singular, int(n != 1)), singular if n == 1 else plural)


def render(source, **context):
    """Render ``source`` with Django's own engine, so ``{% load %}`` goes through installed apps."""
    return Template(source).render(Context(context)).strip()


class XBlockI18nTagLibraryTest(TestCase):
    """
    ``{% load xblock_i18n %}`` works in Django's engine and translates through the block's service.
    """
    TRANS_TEMPLATE = '{% load xblock_i18n %}{% trans "Translate 1" %}'

    def test_app_is_installed(self):
        assert apps.get_app_config("xblock_django_integration").name == "xblock.django"

    def test_trans_uses_the_service(self):
        assert render(self.TRANS_TEMPLATE, **{I18N_SERVICE_CONTEXT_KEY: MockI18nService()}) == "tRaNsLaTe !"

    def test_trans_without_service_uses_django(self):
        assert render(self.TRANS_TEMPLATE) == "Translate 1"

    def test_strings_missing_from_the_service_fall_back_to_django(self):
        # "Yes" is in Django's own catalogs; "Translate 2" is in neither.
        source = '{% load xblock_i18n %}{% trans "Yes" %} {% trans "Translate 2" %}'
        with translation.override("de"):
            assert render(source, **{I18N_SERVICE_CONTEXT_KEY: MockI18nService()}) == "Ja Translate 2"

    def test_blocktrans_plural_uses_the_service(self):
        source = (
            "{% load xblock_i18n %}"
            "{% blocktrans count n=count %}{{ n }} apple{% plural %}{{ n }} apples{% endblocktrans %}"
        )
        service = FakePluralI18nService()
        assert render(source, count=1, **{I18N_SERVICE_CONTEXT_KEY: service}) == "1 manzana"
        assert render(source, count=3, **{I18N_SERVICE_CONTEXT_KEY: service}) == "3 manzanas"

    def test_nothing_leaks_into_the_active_translation(self):
        """
        Rendering the same compiled template repeatedly with a service must not change what Django
        translates afterwards, with or without the service, in this thread.
        """
        template = Template(self.TRANS_TEMPLATE)
        with translation.override("en"):
            active_before = trans_real._active.value  # pylint: disable=protected-access
            for _ in range(3):
                assert template.render(Context({I18N_SERVICE_CONTEXT_KEY: MockI18nService()})).strip() == "tRaNsLaTe !"
                assert template.render(Context({})).strip() == "Translate 1"
                assert translation.gettext("Translate 1") == "Translate 1"
            assert trans_real._active.value is active_before  # pylint: disable=protected-access

    def test_restores_an_unset_active_translation(self):
        """With no active translation, rendering falls back to LANGUAGE_CODE and leaves it unset."""
        translation.deactivate()
        assert not hasattr(trans_real._active, "value")  # pylint: disable=protected-access
        assert render(self.TRANS_TEMPLATE, **{I18N_SERVICE_CONTEXT_KEY: MockI18nService()}) == "tRaNsLaTe !"
        assert not hasattr(trans_real._active, "value")  # pylint: disable=protected-access
