"""
Tests for resources.py
"""


import gettext
import unittest
from unittest.mock import DEFAULT, patch

import importlib.resources

from xblock.utils.resources import ResourceLoader

expected_string = """\
This is a simple template example.

This template can make use of the following context variables:
Name: {{name}}
List: {{items|safe}}

It can also do some fancy things with them:
Default value if name is empty: {{name|default:"Default Name"}}
Length of the list: {{items|length}}
Items of the list:{% for item in items %} {{item}}{% endfor %}

Although it is simple, it can also contain non-ASCII characters:

Thé Fütüré øf Ønlïné Édüçätïøn Ⱡσяєм ι# Før änýøné, änýwhéré, änýtïmé Ⱡσяєм #
"""


example_context = {
    "name": "This is a fine name",
    "items": [1, 2, 3, 4, "a", "b", "c"],
}


expected_filled_template = """\
This is a simple template example.

This template can make use of the following context variables:
Name: This is a fine name
List: [1, 2, 3, 4, 'a', 'b', 'c']

It can also do some fancy things with them:
Default value if name is empty: This is a fine name
Length of the list: 7
Items of the list: 1 2 3 4 a b c

Although it is simple, it can also contain non-ASCII characters:

Thé Fütüré øf Ønlïné Édüçätïøn Ⱡσяєм ι# Før änýøné, änýwhéré, änýtïmé Ⱡσяєм #
"""

expected_not_translated_template = """\

Translate 1

Translate 2

Multi-line translation
with variable: This is a fine name

"""

expected_translated_template = """\

tRaNsLaTe !

Translate 2

mUlTi_LiNe TrAnSlAtIoN: This is a fine name

"""

expected_localized_template = """\

1000
1000
"""

example_id = "example-unique-id"

expected_filled_js_template = """\
<script type='text/template' id='example-unique-id'>
{}
</script>\
""".format(expected_filled_template)

expected_filled_translated_js_template = """\
<script type='text/template' id='example-unique-id'>
{}
</script>\
""".format(expected_translated_template)

expected_filled_not_translated_js_template = """\
<script type='text/template' id='example-unique-id'>
{}
</script>\
""".format(expected_not_translated_template)

expected_filled_localized_js_template = """\
<script type='text/template' id='example-unique-id'>
{}
</script>\
""".format(expected_localized_template)

another_template = """\
<explanation>This is an even simpler xml template.</explanation>
"""


simple_template = """\
<example>
    <title>This is a simple xml template.</title>
    <arguments>
        <url_name>simple_template</url_name>
    </arguments>
</example>
"""


expected_scenarios_with_identifiers = [
    ("another_template", "Another Template", another_template),
    ("simple_template", "Simple Template", simple_template),
]


expected_scenarios = [(t, c) for (i, t, c) in expected_scenarios_with_identifiers]


class MockI18nService:
    """
    I18n service used for testing translations.
    """
    def __init__(self):

        locale_dir = 'data/translations'
        locale_path = str(importlib.resources.files(__package__) / locale_dir)
        domain = 'text'
        self.mock_translator = gettext.translation(
            domain,
            locale_path,
            ['eo'],
        )

    def __getattr__(self, name):
        return getattr(self.mock_translator, name)


class TestResourceLoader(unittest.TestCase):
    """
    Unit Tests for ResourceLoader
    """

    def test_load_unicode(self):
        s = ResourceLoader(__name__).load_unicode("data/simple_django_template.txt")
        self.assertEqual(s, expected_string)

    def test_load_unicode_from_another_module(self):
        s = ResourceLoader("xblock.test.utils.data").load_unicode("simple_django_template.txt")
        self.assertEqual(s, expected_string)

    def test_render_django_template(self):
        loader = ResourceLoader(__name__)
        s = loader.render_django_template("data/simple_django_template.txt", example_context)
        self.assertEqual(s, expected_filled_template)

    def test_render_django_template_translated(self):
        loader = ResourceLoader(__name__)
        s = loader.render_django_template("data/trans_django_template.txt",
                                          context=example_context,
                                          i18n_service=MockI18nService())
        self.assertEqual(s, expected_translated_template)

        # Test that the language changes were reverted
        s = loader.render_django_template("data/trans_django_template.txt", example_context)
        self.assertEqual(s, expected_not_translated_template)

    def test_render_django_template_localized(self):
        # Test that default template tags like l10n are loaded
        loader = ResourceLoader(__name__)
        s = loader.render_django_template("data/l10n_django_template.txt",
                                          context=example_context,
                                          i18n_service=MockI18nService())
        self.assertEqual(s, expected_localized_template)

    def test_render_mako_template(self):
        loader = ResourceLoader(__name__)
        s = loader.render_mako_template("data/simple_mako_template.txt", example_context)
        self.assertEqual(s, expected_filled_template)

    @patch('warnings.warn', DEFAULT)
    def test_render_template_deprecated(self, mock_warn):
        loader = ResourceLoader(__name__)
        s = loader.render_template("data/simple_django_template.txt", example_context)
        self.assertTrue(mock_warn.called)
        self.assertEqual(s, expected_filled_template)

    def test_render_js_template(self):
        loader = ResourceLoader(__name__)
        s = loader.render_js_template("data/simple_django_template.txt", example_id, example_context)
        self.assertEqual(s, expected_filled_js_template)

    def test_render_js_template_translated(self):
        loader = ResourceLoader(__name__)
        s = loader.render_js_template("data/trans_django_template.txt",
                                      example_id,
                                      context=example_context,
                                      i18n_service=MockI18nService())
        self.assertEqual(s, expected_filled_translated_js_template)

        # Test that the language changes were reverted
        s = loader.render_js_template("data/trans_django_template.txt", example_id, example_context)
        self.assertEqual(s, expected_filled_not_translated_js_template)

    def test_render_js_template_localized(self):
        # Test that default template tags like l10n are loaded
        loader = ResourceLoader(__name__)
        s = loader.render_js_template("data/l10n_django_template.txt",
                                      example_id,
                                      context=example_context,
                                      i18n_service=MockI18nService())
        self.assertEqual(s, expected_filled_localized_js_template)

    def test_load_scenarios(self):
        loader = ResourceLoader(__name__)
        scenarios = loader.load_scenarios_from_path("data")
        self.assertEqual(scenarios, expected_scenarios)

    def test_load_scenarios_with_identifiers(self):
        loader = ResourceLoader(__name__)
        scenarios = loader.load_scenarios_from_path("data", include_identifier=True)
        self.assertEqual(scenarios, expected_scenarios_with_identifiers)
