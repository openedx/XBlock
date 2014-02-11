"""An XBlock checking container/block relationships for correctness."""

import logging
import pkg_resources
import random
import webob
from itertools import chain

from xblock.core import XBlock
from xblock.fields import Scope, Dict, Boolean
from xblock.fragment import Fragment


def generate_fields(cls):
    """
    A class decorator that generates fields for all field scopes.
    These fields are Dicts, and map usage_ids to values.
    """
    for scope in Scope.scopes():
        setattr(cls, scope.name, Dict(
            help="Values stored in the {} scope".format(scope),
            scope=scope
        ))

    return cls


class SuccessResponse(webob.Response):
    """
    Standardized response for successful tests
    """
    def __init__(self, data):
        """
        Args:
            data (dict): The data to return to the client (must be jsonable)
        """
        data['status'] = 'ok'
        super(SuccessResponse, self).__init__(json=data)


class FailureResponse(webob.Response):
    """
    Standardized response for unsuccessful tests
    """
    def __init__(self, message):
        """
        Args:
            message (str): The error message to return to the client
        """
        super(FailureResponse, self).__init__(json={'status': 'error', 'message': message})


@generate_fields
class AcidBlock(XBlock):
    """
    A testing block that checks the behavior of the container.
    """

    SUCCESS_CLASS = 'fa fa-check-square-o fa-lg pass'
    FAILURE_CLASS = 'fa fa-times fa-lg fail'
    ERROR_CLASS = 'fa fa-exclamation-triangle fa-lg error'
    UNKNOWN_CLASS = 'fa fa-question-circle fa-lg unknown'

    enabled_fields = Dict(
        help="Dictionary specifying which fields should be enabled for which views. If a view is left out, all fields are enabled",
        scope=Scope.content,
        default={
            'studio_view': ['content', 'settings'],
            'student_view': ['user_state', 'user_state_summary', 'preferences', 'user_info']
        }
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def setup_storage(self, scope):
        """
        Set up the block for a storage test of the specified scope.

        This updates the field named scope with an entry keyed on
        this block's `usage_id`, set to a random integer.

        Args:
            scope (str): The name of the scope to test

        Returns:
            dict: A dictionary with the following keys:
                scope: the name of the scope under test
                value: the new randomly generated value
                query: a query string encoding the scope and value
                suffix: a suffix encoding the value
                handler_url: a server-generated handler url that, when called, will verify
                    storage for the specified `scope`
        """
        new_value = random.randint(0, 9999)

        # Retrieve the field named for the scope (whose value is a dictionary)
        # and add an entry for this block's usage_id, set to `new_value`.
        getattr(self, scope)[str(self.scope_ids.usage_id)] = new_value

        query = 'QUERY={}&SCOPE={}'.format(new_value, scope)
        suffix = 'SUFFIX{}'.format(new_value)

        return {
            'scope': scope,
            'value': new_value,
            'query': query,
            'suffix': suffix,
            'handler_url': self.runtime.handler_url(self, 'check_storage', suffix, query)
        }

    def fallback_view(self, view_name, context=None):               # pylint: disable=W0613
        """
        This view is used by the Acid XBlock to test various features of
        the runtime it is contained in
        """
        block_template = self.resource_string("static/html/acid.html")
        storage_test_template = self.resource_string('static/html/scope_storage_test.html')

        scopes = (
            scope
            for scope in Scope.scopes()
            if (view_name not in self.enabled_fields
                or scope.name in self.enabled_fields[view_name])
        )

        scope_test_contexts = []
        for scope in scopes:
            try:
                scope_test_contexts.append(self.setup_storage(scope.name))
            except Exception as exc:
                logging.warning('Unable to use scope in acid test', exc_info=True)

        frag = Fragment(block_template.format(
            error_class=self.ERROR_CLASS,
            success_class=self.SUCCESS_CLASS,
            failure_class=self.FAILURE_CLASS,
            unknown_class=self.UNKNOWN_CLASS,
            storage_tests='\n'.join(
                storage_test_template.format(
                    alt="alt" if idx % 2 else "",
                    unknown_class=self.UNKNOWN_CLASS,
                    **context
                )
                for idx, context in enumerate(scope_test_contexts)
            ),
        ))

        frag.add_javascript(self.resource_string("static/js/jquery.ajaxq-0.0.1.js"))
        frag.add_javascript(self.resource_string('static/js/acid.js'))
        frag.add_css(self.resource_string("static/css/acid.css"))
        frag.add_css_url('//netdna.bootstrapcdn.com/font-awesome/4.0.3/css/font-awesome.css')
        frag.initialize_js('AcidBlock')
        return frag

    @XBlock.handler
    def check_storage(self, request, suffix=''):
        """
        Verifies that scoped storage is working correctly, and that handler_urls
        are generated correctly by both the client- and server-side runtimes.

        Args:
            request (:class:`webob.Request`): The incoming request
            suffix (`str`): The suffix that the handler was called with
        """

        if 'SCOPE' not in request.GET:
            return FailureResponse("SCOPE is missing from query parameters")

        scope = request.GET['SCOPE']

        if 'QUERY' not in request.GET:
            return FailureResponse("QUERY is missing from query parameters")

        stored_value = getattr(self, scope).get(str(self.scope_ids.usage_id))
        query_value = int(request.GET['QUERY'])

        if stored_value != query_value:
            return FailureResponse(
                "Stored value {!r} doesn't match supplied QUERY {!r}".format(
                    stored_value,
                    query_value
                )
            )

        if not suffix.startswith("SUFFIX"):
            return FailureResponse("suffix is wrong: {!r}".format(suffix))

        suffix_value = int(suffix[6:])

        if stored_value != suffix_value:
            return FailureResponse(
                "Stored value {!r} doesn't match supplied SUFFIX {!r}".format(
                    stored_value,
                    suffix_value
                )
            )

        if 'VALUE' not in request.POST:
            return FailureResponse('VALUE is missing from posted data')

        posted_value = int(request.POST['VALUE'])

        if stored_value != posted_value:
            return FailureResponse(
                "Stored value {!r} doesn't match posted VALUE {!r}".format(
                    stored_value,
                    posted_value
                )
            )

        return SuccessResponse(self.setup_storage(scope))

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("XBlock Acid test",
             """\
                <vertical_demo>
                    <acid/>
                    <acid/>
                    <acid/>
                </vertical_demo>
             """)
        ]
