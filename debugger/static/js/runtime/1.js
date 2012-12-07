// XBlock runtime implementation.

// Constructor for a runtime object provided to an XBlock init function.
function runtime_1(element, children) {
    var child_map = {}
    $.each(children, function(idx, child) {
        child_map[child.name] = child
    });
    return {
        handler_url: function(handler_name) {
            var usage = $(element).data('usage');
            return "/" + usage + "/" + handler_name;
        },
        children: children,
        child_map: child_map
    }
}

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

    function initializeBlock(element) {
        var children = initializeBlocks($(element));

        var version = $(element).data('runtime-version');
        if (version === undefined) {
            return null;
        }

        var runtime = window['runtime_' + version](element, children);
        var init_fn = window[$(element).data('init')];
        var js_block = init_fn(runtime, element) || {};
        js_block.element = element;
        js_block.name = $(element).data('name');
        return js_block;
    }

    function initializeBlocks(element) {
        return $(element).immediateDescendents('.xblock').map(function(idx, elem) {
            return initializeBlock(elem);
        }).toArray();
    }

    $('body').on('ajaxSend', function(elm, xhr, s) {
        // Pass along the Django-specific CSRF token.
        xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
    });

    initializeBlocks($('body'));
});
