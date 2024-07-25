"""
Helper class (ResourceLoader) for loading resources used by an XBlock
"""
import os
import sys
import warnings

import importlib.resources
from django.template import Context, Engine, Template
from django.template.backends.django import get_installed_libraries
from mako.lookup import TemplateLookup as MakoTemplateLookup
from mako.template import Template as MakoTemplate


class ResourceLoader:
    """Loads resources relative to the module named by the module_name parameter."""
    def __init__(self, module_name):
        self.module_name = module_name

    def load_unicode(self, resource_path):
        """
        Gets the content of a resource
        """
        package_name = importlib.import_module(self.module_name).__package__
        # TODO: Add encoding on other places as well
        # resource_path should be a relative path, but historically some callers passed it in
        # with a leading slash, which pkg_resources tolerated and ignored. importlib is less
        # forgiving, so in order to maintain backwards compatibility, we must strip off the
        # leading slash is there is one to ensure we actually have a relative path.
        return importlib.resources.files(package_name).joinpath(resource_path.lstrip('/')).read_text(encoding="utf-8")

    def render_django_template(self, template_path, context=None, i18n_service=None):
        """
        Evaluate a django template by resource path, applying the provided context.
        """
        context = context or {}
        context['_i18n_service'] = i18n_service
        libraries = {
            'i18n': 'xblock.utils.templatetags.i18n',
        }

        installed_libraries = get_installed_libraries()
        installed_libraries.update(libraries)
        engine = Engine(libraries=installed_libraries)

        template_str = self.load_unicode(template_path)
        template = Template(template_str, engine=engine)
        rendered = template.render(Context(context))

        return rendered

    def render_mako_template(self, template_path, context=None):
        """
        Evaluate a mako template by resource path, applying the provided context
        Note: This function has been deprecated. Consider using Django templates or React UI instead of mako.
        """
        warnings.warn(
            'ResourceLoader.render_mako_template has been deprecated. '
            'Use Django templates or React UI instead of mako.',
            DeprecationWarning, stacklevel=3,
        )
        context = context or {}
        template_str = self.load_unicode(template_path)

        package_name = importlib.import_module(self.module_name).__package__
        directory = str(importlib.resources.files(package_name))
        lookup = MakoTemplateLookup(directories=[directory])
        template = MakoTemplate(template_str, lookup=lookup)
        return template.render(**context)

    def render_template(self, template_path, context=None):
        """
        This function has been deprecated. It calls render_django_template to support backwards compatibility.
        """
        warnings.warn(
            "ResourceLoader.render_template has been deprecated in favor of ResourceLoader.render_django_template"
        )
        return self.render_django_template(template_path, context)

    def render_js_template(self, template_path, element_id, context=None, i18n_service=None):
        """
        Render a js template.
        """
        context = context or {}
        return "<script type='text/template' id='{}'>\n{}\n</script>".format(
            element_id,
            self.render_django_template(template_path, context, i18n_service)
        )

    def load_scenarios_from_path(self, relative_scenario_dir, include_identifier=False):
        """
        Returns an array of (title, xmlcontent) from files contained in a specified directory,
        formatted as expected for the return value of the workbench_scenarios() method.

        If `include_identifier` is True, returns an array of (identifier, title, xmlcontent).
        """
        base_dir = os.path.dirname(os.path.realpath(sys.modules[self.module_name].__file__))
        scenario_dir = os.path.join(base_dir, relative_scenario_dir)

        scenarios = []
        if os.path.isdir(scenario_dir):
            for template in sorted(os.listdir(scenario_dir)):
                if not template.endswith('.xml'):
                    continue
                identifier = template[:-4]
                title = identifier.replace('_', ' ').title()
                template_path = os.path.join(relative_scenario_dir, template)
                scenario = str(self.render_django_template(template_path, {"url_name": identifier}))
                if not include_identifier:
                    scenarios.append((title, scenario))
                else:
                    scenarios.append((identifier, title, scenario))

        return scenarios
