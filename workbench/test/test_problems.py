"""Test that problems and problem submission works well."""

from workbench import scenarios
from workbench.test.selenium_test import SeleniumTest


class ProblemInteractionTest(SeleniumTest):
    """
    A browser-based test of answering problems right and wrong.
    """

    def setUp(self):
        super(ProblemInteractionTest, self).setUp()

        one_problem = """
            <problem>
                <html><p class="the_numbers">$a $b</p></html>
                <textinput name="sum_input" input_type="int" />
                <equality name="sum_checker" left="./sum_input/@student_input" right="$c" />
                <script>
                    import random
                    a = random.randint(1, 1000000)
                    b = random.randint(1, 1000000)
                    c = a + b
                </script>
            </problem>
            """
        self.num_problems = 3
        scenarios.add_xml_scenario(
            "test_many_problems", "Many problems",
            "<vertical>" + one_problem * self.num_problems + "</vertical>"
        )
        self.addCleanup(scenarios.remove_scenario, "test_many_problems")

    def test_many_problems(self):
        # Test that problems work properly.
        self.browser.get(self.live_server_url + "/scenario/test_many_problems")
        header1 = self.browser.find_element_by_css_selector("h1")
        self.assertEqual(header1.text, "XBlock: Many problems")

        # Find the numbers on the page.
        nums = self.browser.find_elements_by_css_selector("p.the_numbers")
        num_pairs = [tuple(int(n) for n in num.text.split()) for num in nums]
        # They should be all different.
        self.assertEqual(len(set(num_pairs)), self.num_problems)

        text_ctrls_xpath = '//div[@data-block-type="textinput"][@data-name="sum_input"]/input'
        text_ctrls = self.browser.find_elements_by_xpath(text_ctrls_xpath)
        check_btns = self.browser.find_elements_by_css_selector('input.check')
        right_wrongs = self.browser.find_elements_by_css_selector('span.indicator')

        for i in range(self.num_problems):
            # Before answering, the indicator says Not Attempted.
            self.assertIn("Not attempted", right_wrongs[i].text)

            answer = sum(num_pairs[i])

            for _ in range(2):
                # Answer right.
                text_ctrls[i].clear()
                text_ctrls[i].send_keys(str(answer))
                check_btns[i].click()
                img = right_wrongs[i].find_element_by_css_selector("img")
                self.assertIn("/correct-icon.png", img.get_attribute("src"))

                # Answer wrong.
                text_ctrls[i].clear()
                text_ctrls[i].send_keys(str(answer + 1))
                check_btns[i].click()
                img = right_wrongs[i].find_element_by_css_selector("img")
                self.assertIn("/incorrect-icon.png", img.get_attribute("src"))
