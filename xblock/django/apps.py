"""
Django app configuration for XBlock.
"""

from django.apps import AppConfig


class XBlockDjangoConfig(AppConfig):
    """
    Add ``"xblock.django"`` to ``INSTALLED_APPS`` to get XBlock's Django integration pieces that Django
    only discovers through installed apps.

    Currently that is the ``xblock_i18n`` template tag library (``{% load xblock_i18n %}``), whose
    ``trans`` and ``blocktrans`` translate through the XBlock i18n service found in the template context.
    Blocks whose templates are rendered by Django's own engine (rather than by
    ``xblock.utils.resources.ResourceLoader``) need it.
    """

    name = "xblock.django"
    label = "xblock_django_integration"
    verbose_name = "XBlock Django integration"
