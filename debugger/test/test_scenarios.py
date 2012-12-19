"""Test that all scenarios render successfully."""

import re

import lxml.html

from django.test.client import Client


def test_all_scenarios():
    # Load the home page, get every URL, make a test from it.
    c = Client()
    response = c.get("/")
    assert response.status_code == 200
    html = lxml.html.fromstring(response.content)
    for a in html.xpath('//a'):
        yield try_scenario, a.get('href'), a.text


def try_scenario(url, text):
    # Check that the scenario renders without error.
    c = Client()
    response = c.get(url, follow=True)
    assert response.status_code == 200, text
