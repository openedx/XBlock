"""An XBlock checking container/block relationships for correctness."""

import pkg_resources
import random
import webob
from itertools import chain

from xblock.core import XBlock
from xblock.fields import Scope, Integer
from xblock.fragment import Fragment


REQUIRED_SCOPES = {
    'student_view': ['user_state'],
    'studio_view': ['settings', 'content']
}


def generate_fields(cls):
    """
    Generate fields for any scope listed in REQUIRED_SCOPES
    """
    for scope in set(chain(*REQUIRED_SCOPES.values())):
        setattr(cls, scope, Integer(
            help="A value stored in the {} scope".format(scope),
            default=None,
            scope=getattr(Scope, scope)
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

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def setup_storage(self, scope):
        """
        Set up the block for a storage test of the specified scope.

        This sets the value for the field named `scope` to a random value.

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
        setattr(self, scope, new_value)

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

        frag = Fragment(block_template.format(
            storage_tests='\n'.join(
                storage_test_template.format(**self.setup_storage(scope))
                for scope in REQUIRED_SCOPES[view_name]
            ),
        ))

        frag.add_javascript(self.resource_string("static/js/src/acid.js"))
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

        stored_value = getattr(self, scope)
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
