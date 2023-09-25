"""
Template tags for handling i18n translations for xblocks

Based on: https://github.com/eduNEXT/django-xblock-i18n
"""

from contextlib import contextmanager

from django.template import Library, Node
from django.templatetags import i18n
from django.utils.translation import get_language, trans_real

register = Library()


class ProxyTransNode(Node):
    """
    This node is a proxy of a django TranslateNode.
    """
    def __init__(self, do_translate_node):
        """
        Initialize the ProxyTransNode
        """
        self.do_translate = do_translate_node
        self._translations = {}

    @contextmanager
    def merge_translation(self, context):
        """
        Context wrapper which modifies the given language's translation catalog using the i18n service, if found.
        """
        language = get_language()
        i18n_service = context.get('_i18n_service', None)
        if i18n_service:
            # Cache the original translation object to reduce overhead
            if language not in self._translations:
                self._translations[language] = trans_real.DjangoTranslation(language)

            translation = trans_real.translation(language)
            translation.merge(i18n_service)

        yield

        # Revert to original translation object
        if language in self._translations:
            trans_real._translations[language] = self._translations[language]  # pylint: disable=protected-access
            # Re-activate the current language to reset translation caches
            trans_real.activate(language)

    def render(self, context):
        """
        Renders the translated text using the XBlock i18n service, if available.
        """
        with self.merge_translation(context):
            django_translated = self.do_translate.render(context)

        return django_translated


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
