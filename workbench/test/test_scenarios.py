"""Test that all scenarios render successfully."""

import lxml.html

from django.test.client import Client


def test_all_scenarios():
    """Load the home page, get every URL, make a test from it."""
    client = Client()
    response = client.get("/")
    assert response.status_code == 200
    html = lxml.html.fromstring(response.content)
    for a_tag in html.xpath('//a'):
        yield try_scenario, a_tag.get('href'), a_tag.text


def try_scenario(url, name):
    """Check that a scenario renders without error.

    `url`: the URL to the scenario to test.

    `name`: the name of the scenario, used in error messages.

    """
    client = Client()
    response = client.get(url, follow=True)
    assert response.status_code == 200, name
