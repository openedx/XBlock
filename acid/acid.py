"""An XBlock checking container/block relationships for correctness."""

import pkg_resources

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment


class AcidBlock(XBlock):
    """
    A testing block that checks the behavior of the container.
    """

    rand9999 = String(help="A random value", default="def", scope=Scope.user_state)

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, context=None):               # pylint: disable=W0613
        frag = Fragment(self.resource_string("static/html/acid.html"))
        frag.add_javascript(self.resource_string("static/js/src/acid.js"))
        frag.initialize_js('AcidBlock')
        return frag

    @XBlock.json_handler
    def handler1(self, data, suffix=''):
        """The first handler hit by the browser when the block is loaded."""
        ret = {
            "status": "bad",
            "data": data,
            "suffix": suffix,
        }

        if not suffix.startswith("SUFFIX"):
            ret["message"] = "suffix is wrong: %r" % suffix
            return ret

        suffix_rand9999 = suffix[6:]
        rand9999 = str(data['rand9999'])
        ret["rand9999"] = rand9999
        if suffix_rand9999 != rand9999:
            ret["message"] = "suffix doesn't match rand9999: %r != %r" % (suffix, rand9999)
            return ret

        self.rand9999 = rand9999
        ret["status"] = "ok"
        return ret

    @XBlock.json_handler
    def handler2(self, data, suffix=''):
        """The second handler hit by the browser when the block is loaded."""
        ret = {
            "status": "bad",
            "data": data,
            "suffix": suffix,
        }
        rand9999 = str(data['rand9999'])
        if self.rand9999 != rand9999:
            ret["message"] = "stored rand9999 doesn't match rand9999: %r != %r" % (self.rand9999, rand9999)
            return ret

        ret["status"] = "ok"
        return ret

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("XBlock Acid test",
             """\
                <vertical>
                    <acid/>
                    <acid/>
                    <acid/>
                </vertical>
             """)
        ]
