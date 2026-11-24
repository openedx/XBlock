"""
Template tags for handling i18n translations for xblocks

Based on: https://github.com/eduNEXT/django-xblock-i18n

``trans`` and ``blocktrans`` here behave like Django's, except that when the template context
holds an XBlock i18n service under the ``_i18n_service`` key, strings in that service's catalog
are translated by it. Everything else falls through to Django's own translation for the active
language.

This library is loadable in two ways:

* ``xblock.utils.resources.ResourceLoader.render_django_template`` maps both ``{% load i18n %}``
  and ``{% load xblock_i18n %}`` to it.
* With ``xblock.django`` in ``INSTALLED_APPS``, Django's own template engine finds it as
  ``{% load xblock_i18n %}``.
"""

from contextlib import contextmanager

from django.conf import settings
from django.template import Library, Node
from django.templatetags import i18n
from django.utils.translation import trans_real
from django.utils.translation.trans_real import CONTEXT_SEPARATOR

I18N_SERVICE_CONTEXT_KEY = "_i18n_service"

register = Library()

_UNSET = object()


class BlockFirstTranslation:
    """
    A translation object that tries an XBlock i18n service first, then another translation object.

    It implements the parts of the ``gettext.NullTranslations`` interface that Django's translation
    functions call on the active translation object.
    """

    def __init__(self, i18n_service, fallback):
        self._service = i18n_service
        self._fallback = fallback
        # A GNUTranslations-style catalog: a mapping from msgid (or (msgid, plural index)) to
        # translation. Services without one, such as xblock.runtime.NullI18nService, translate nothing.
        self._catalog = getattr(i18n_service, "_catalog", None) or {}

    def gettext(self, message):
        if message in self._catalog:
            return self._service.gettext(message)
        return self._fallback.gettext(message)

    def ngettext(self, msgid1, msgid2, n):
        if (msgid1, 0) in self._catalog or (msgid1, 1) in self._catalog:
            return self._service.ngettext(msgid1, msgid2, n)
        return self._fallback.ngettext(msgid1, msgid2, n)

    def pgettext(self, context, message):
        if f"{context}{CONTEXT_SEPARATOR}{message}" in self._catalog:
            return self._service.pgettext(context, message)
        return self._fallback.pgettext(context, message)

    def npgettext(self, context, msgid1, msgid2, n):
        key = f"{context}{CONTEXT_SEPARATOR}{msgid1}"
        if (key, 0) in self._catalog or (key, 1) in self._catalog:
            return self._service.npgettext(context, msgid1, msgid2, n)
        return self._fallback.npgettext(context, msgid1, msgid2, n)

    def to_language(self):
        return self._fallback.to_language()

    def language(self):
        return self._fallback.language()


@contextmanager
def block_translation(i18n_service):
    """
    Make ``i18n_service`` the first place Django's translation functions look, for the current thread.

    Django's ``{% trans %}`` and ``{% blocktrans %}`` call ``django.utils.translation.gettext`` and
    friends, which consult the thread-local active translation object. This installs a
    ``BlockFirstTranslation`` wrapping the current one for the duration of the block, and puts the
    previous object back afterwards. Nothing shared is modified, so nothing leaks between renders
    or between blocks.
    """
    previous = getattr(trans_real._active, "value", _UNSET)  # pylint: disable=protected-access
    fallback = previous if previous is not _UNSET else trans_real.translation(settings.LANGUAGE_CODE)
    trans_real._active.value = BlockFirstTranslation(i18n_service, fallback)  # pylint: disable=protected-access
    try:
        yield
    finally:
        if previous is _UNSET:
            del trans_real._active.value  # pylint: disable=protected-access
        else:
            trans_real._active.value = previous  # pylint: disable=protected-access


class ProxyTransNode(Node):
    """
    This node is a proxy of a django TranslateNode.
    """
    def __init__(self, do_translate_node):
        """
        Initialize the ProxyTransNode
        """
        self.do_translate = do_translate_node

    def render(self, context):
        """
        Renders the translated text using the XBlock i18n service, if available.
        """
        i18n_service = context.get(I18N_SERVICE_CONTEXT_KEY, None)
        if not i18n_service:
            return self.do_translate.render(context)
        with block_translation(i18n_service):
            return self.do_translate.render(context)


@register.tag('trans')
def xblock_translate(parser, token):
    """
    Proxy implementation of the i18n `trans` tag.
    """
    return ProxyTransNode(i18n.do_translate(parser, token))


@register.tag('blocktrans')
def xblock_translate_block(parser, token):
    """
    Proxy implementation of the i18n `blocktrans` tag.
    """
    return ProxyTransNode(i18n.do_block_translate(parser, token))
