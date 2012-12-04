function runtime_1(element, children) {
    return {
        handler_url: function(handler_name) {
            var usage = $(element).data('usage');
            return "/" + usage + "/" + handler_name;
        },
        prep_xml_http_request: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
        },
        children: children
    }
}
