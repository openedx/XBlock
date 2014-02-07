/* Javascript for the Acid XBlock. */
function AcidBlock(runtime, element) {

    function mark(result, selector, subelem) {
        var elems = $(selector, subelem || element)
        if (elems.length == 1) {
            $("<i/>", {
                'class': $('.acid-block', element).data(result + '-class')
            }).appendTo(elems.empty());
        } else {
            $("<i/>", {
                'class': $('.acid-block', element).data('error-class')
            }).after("ASSERTION FAILURE: Can only mark single elements").appendTo(elems.empty())
            console.log(elems);
        }
    }

    mark('success', '.js-init-run');

    $(function ($) {
        mark('success', '.document-ready-run');

        $('.scope-storage-test', element).each(function() {
            var $this = $(this);
            $.ajaxq("acid_queue", {
                type: "POST",
                data: {"VALUE": $this.data('value')},
                url: $this.data('handler-url'),
                success: function (ret) {
                    mark('success', '.server-storage-test-returned', $this);
                    if (ret.status == "ok") {
                        mark('success', '.server-storage-test-succeeded', $this);

                        $.ajaxq("acid_queue", {
                            type: "POST",
                            data: {"VALUE": ret.value},
                            url: runtime.handlerUrl(element, "check_storage", ret.suffix, ret.query),
                            success: function (ret) {
                                mark('success', '.client-storage-test-returned', $this);

                                if (ret.status == "ok") {
                                    mark('success', '.client-storage-test-succeeded', $this);
                                } else {
                                    mark('failure', '.client-storage-test-succeeded', ret.message, $this);
                                }
                            }
                        });
                    } else {
                        mark('failure', '.server-storage-test-succeeded', ret.message, $this);
                    }
                }
            });
        });
    });
}
