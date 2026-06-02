#!/usr/bin/env python

"""
Provides a URL for testing
"""
from django.urls import path

from web_fragments.examples.views import EXAMPLE_FRAGMENT_VIEW_NAME, ExampleFragmentView

urlpatterns = [
    path('test_fragment', ExampleFragmentView.as_view(), name=EXAMPLE_FRAGMENT_VIEW_NAME),
]
