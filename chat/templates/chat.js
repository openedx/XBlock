function initializeChat() {
    Candy.init("http://{{jabber_domain}}:5280/http-bind/", {
        core: {
            debug: true,
            autojoin: ["{{chat_room}}@conference.{{jabber_domain}}"]
        },
        view: { resources: "{{candy_resources}}/"}
    });
    Candy.Core.connect("{{nick}}", "{{password}}");
}
