// XBlock runtime implementation.

var XBlock = (function () {

    // Constructors for a runtime object provided to an XBlock init function.
    // Indexed by version number.  Only 1 right now.
    var runtimeConstructors = {
        1: function (element, children) {
            var childMap = {}
            $.each(children, function(idx, child) {
                childMap[child.name] = child
            });
            return {
                handlerUrl: function(handlerName) {
                    var usage = $(element).data('usage');
                    return "/handler/" + usage + "/" + handlerName + "/?student=" + studentId;
                },
                children: children,
                childMap: childMap
            };
        }
    };

    var initializeBlock = function (element) {
        var children = initializeBlocks($(element));

        var version = $(element).data('runtime-version');
        if (version === undefined) {
            return null;
        }

        var runtime = runtimeConstructors[version](element, children);
        var initFn = window[$(element).data('init')];
        var jsBlock = initFn(runtime, element) || {};
        jsBlock.element = element;
        jsBlock.name = $(element).data('name');
        return jsBlock;
    };

    var initializeBlocks = function (element) {
        return $(element).immediateDescendents('.xblock').map(function(idx, elem) {
            return initializeBlock(elem);
        }).toArray();
    };

    return {
        initializeBlocks: initializeBlocks
    };
}());


$(function() {
    // Find all the children of an element that match the selector, but only
    // the first instance found down any path.  For example, we'll find all
    // the ".xblock" elements below us, but not the ones that are themselves
    // contained somewhere inside ".xblock" elements.
    $.fn.immediateDescendents = function(selector) {
        return this.children().map(function(idx, element) {
            if ($(element).is(selector)) {
                return element;
            } else {
                return $(element).immediateDescendents(selector).toArray();
            }
        });
    };

    $('body').on('ajaxSend', function(elm, xhr, s) {
        // Pass along the Django-specific CSRF token.
        xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
    });

    XBlock.initializeBlocks($('body'));
});
