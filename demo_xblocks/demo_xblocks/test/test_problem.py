"""
Tests of the Problem XBlock, and its components.
"""

import json

import webob

from xblock.test.tools import assert_equals

from workbench.runtime import WorkbenchRuntime


def make_request(body):
    """Mock request method."""
    request = webob.Request({})
    request.body = body
    return request


def text_of_response(response):
    """Return the text of response."""
    return "".join(response.app_iter)


def test_problem_submission():
    runtime = WorkbenchRuntime()

    # WorkbenchRuntime has an id_generator, but most runtimes won't
    # (because the generator will be contextual), so we
    # pass it explicitly to parse_xml_string.
    problem_usage_id = runtime.parse_xml_string("""
        <problem_demo>
            <textinput_demo name='vote_count' input_type='int'/>

            <script>
                numvotes = 4
            </script>
            <equality_demo name='votes_named' left='./vote_count/@student_input' right='$numvotes'>
                Number of upvotes matches entered string
            </equality_demo>
        </problem_demo>
    """, runtime.id_generator)
    problem = runtime.get_block(problem_usage_id)
    json_data = json.dumps({"vote_count": [{"name": "input", "value": "4"}]})
    resp = runtime.handle(problem, 'check', make_request(json_data))
    resp_data = json.loads(text_of_response(resp))
    assert_equals(resp_data['checkResults']['votes_named'], True)
