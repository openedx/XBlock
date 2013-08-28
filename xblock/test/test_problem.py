"""
Tests of the Problem XBlock, and its components.
"""

import json

import webob

from nose.tools import assert_equals  # pylint: disable=E0611

from xblock.parse import parse_xml_string
from workbench.runtime import Usage, WorkbenchRuntime


def make_request(body):
    """Mock request method."""
    request = webob.Request({})
    request.body = body
    return request


def text_of_response(response):
    """Return the text of response."""
    return "".join(response.app_iter)


def test_problem_submission():
    problem_usage = parse_xml_string("""
        <problem>
            <textinput name='vote_count' input_type='int'/>

            <script>
                numvotes = 4
            </script>
            <equality name='votes_named' left='./vote_count/@student_input' right='$numvotes'>
                Number of upvotes matches entered string
            </equality>
        </problem>
    """, Usage)
    problem_usage.store_initial_state()
    runtime = WorkbenchRuntime()
    problem = runtime.create_xblock(problem_usage)
    json_data = json.dumps({"vote_count": [{"name": "input", "value": "4"}]})
    resp = runtime.handle(problem, 'check', make_request(json_data))
    resp_data = json.loads(text_of_response(resp))
    assert_equals(resp_data['check_results']['votes_named'], True)
