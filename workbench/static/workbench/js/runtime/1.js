// XBlock runtime implementation.


var RuntimeProvider = (function() {

  var getRuntime = function(version) {
    if (! this.versions.hasOwnProperty(version)) {
      throw 'Unsupported XBlock version: ' + version;
    }
    return this.versions[version];
  };

  var versions = {
    1: {
      handlerUrl: function(block, handlerName, suffix, query) {
        suffix = typeof suffix !== 'undefined' ? suffix : '';
        query = typeof query !== 'undefined' ? query : '';
        var usage = $(block).data('usage');

        // studentId and handlerBaseUrl are both defined in block.html
        return (handlerBaseUrl + usage +
                           "/" + handlerName +
                           "/" + suffix +
                   "?student=" + studentId +
                           "&" + query);
      },
      children: function(block) {
        return $(block).prop('xblock_children');
      },
      childMap: function(block, childName) {
        var children = this.children(block);
        for (var i = 0; i < children.length; i++) {
          var child = children[i];
          if (child.name == childName) {
            return child
          }
        }
      }
    }
  };

  return {
    getRuntime: getRuntime,
    versions: versions
  };
}());


var XBlock = (function () {

    var initializeBlock = function (element) {
        $(element).prop('xblock_children', initializeBlocks($(element)));

        var version = $(element).data('runtime-version');
        if (version === undefined) {
            return null;
        }

        var runtime = RuntimeProvider.getRuntime(version);
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
