/* Javascript for the Acid XBlock. */
function AcidBlock(runtime, element) {

    function mark_yes(selector, subelem) {
        var elems = $(selector, subelem || element)
        if (elems.length == 1) {
            elems.text("yes")
        } else {
            elem.text("ASSERTION FAILURE: Can only mark_yes single elements");
            console.log(elems);
        }
    }

    function mark_no(selector, message, subelem) {
        var elems = $(selector, subelem || element)
        if (elems.length == 1) {
            elems.text("no: " + message)
        } else {
            elem.text("ASSERTION FAILURE: Can only mark_no single elements");
            console.log(elems);
        }
    }

    mark_yes('.js_init_run');

    $(function ($) {
        mark_yes('.document_ready_run');

        $('.scope-storage-test', element).each(function() {
            var $this = $(this);
            $.ajax({
                type: "POST",
                data: {"VALUE": $this.data('value')},
                url: $this.data('handler-url'),
                success: function (ret) {
                    mark_yes('.server-storage-test-returned', $this);
                    if (ret.status == "ok") {
                        mark_yes('.server-storage-test-succeeded', $this);

                        $.ajax({
                            type: "POST",
                            data: {"VALUE": ret.value},
                            url: runtime.handlerUrl(element, "check_storage", ret.suffix, ret.query),
                            success: function (ret) {
                                mark_yes('.client-storage-test-returned', $this);

                                if (ret.status == "ok") {
                                    mark_yes('.client-storage-test-succeeded', $this);
                                } else {
                                    mark_no('.client-storage-test-succeeded', ret.message, $this);
                                }
                            }
                        });
                    } else {
                        mark_no('.server-storage-test-succeed', ret.message, $this);
                    }
                }
            });
        });
    });
}
