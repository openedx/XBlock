function runtime_1(element) {
    return {
        handler: function(handler_name) {
            var module_type = $(element).data('module-type');
            return "/" + module_type + "/" + handler_name;
        },
        prep_xml_http_request: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
        }
    }
}