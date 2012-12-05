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
        prep_xml_http_request: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
        },
        children: children,
        child_map: child_map
    }
}
