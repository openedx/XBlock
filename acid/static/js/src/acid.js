/* Javascript for the Acid XBlock. */
function AcidBlock(runtime, element) {

    function mark_yes(selector) {
        $(selector, element).text("yes");
    };

    function mark_no(selector, message) {
        $(selector, element).text("no: " + message);
    }

    function make_rand9999() {
        return Math.floor((Math.random()*10000));
    };

    mark_yes('.js_init_run');

    $(function ($) {
        mark_yes('.document_ready_run');
        var rand9999 = make_rand9999();

        /* Immediately ping a handler. */
        $.ajax({
            type: "POST",
            url: runtime.handlerUrl(element, "handler1", "SUFFIX"+rand9999),
            data: JSON.stringify({rand9999: rand9999}),
            success: function (ret) {
                mark_yes('.handler1_returned');
                if (ret.status == "ok") {
                    mark_yes('.handler1_succeeded');

                    $.ajax({
                        type: "POST",
                        url: runtime.handlerUrl(element, "handler2"),
                        data: JSON.stringify({rand9999: rand9999}),
                        success: function (ret) {
                            mark_yes('.handler2_returned');
                            if (ret.status == "ok") {
                                mark_yes('.handler2_succeeded');
                            }
                            else {
                                mark_no('.handler2_succeeded', ret.message);
                            }
                        }
                    });
                }
                else {
                    mark_no('.handler1_succeeded', ret.message);
                }
            }
        });
    });
}
