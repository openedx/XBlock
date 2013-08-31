"""Helpers for Selenium tests."""

from django.test import LiveServerTestCase
from selenium import webdriver

from nose.plugins.attrib import attr

from workbench.runtime import MEMORY_KVS


@attr('selenium')
class SeleniumTest(LiveServerTestCase):
    """Base test class that provides setUpClass and tearDownClass
    methods necessary for selenium testing."""

    @classmethod
    def setUpClass(cls):
        super(SeleniumTest, cls).setUpClass()
        cls.browser = webdriver.Firefox()
        cls.browser.implicitly_wait(1)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(SeleniumTest, cls).tearDownClass()

    def setUp(self):
        super(SeleniumTest, self).setUp()

        # Clear the in-memory key value store
        MEMORY_KVS.clear()
