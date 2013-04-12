var CandyShop = (function(self) { return self; }(CandyShop || {}));

CandyShop.Class2Go = (function(self, Candy, $) {

    self.init = function() {
        Candy.View.Event.Room.onAdd = function(roomPane) {
            var roomJid = roomPane['roomJid'];
            var roomType = roomPane['type'];

            var roomTabClass;
            if (roomType === 'groupchat') {
                roomTabClass = 'icon-group';
                roomTabCloseClass = 'hidden';
            } else {
                roomTabClass = 'icon-user';
                roomTabCloseClass = '';
            }

            var roomTab = $('#chat-tabs li[data-roomjid="' + roomJid + '"]').find('.label');
            roomTab.attr('title', roomTab.text()).html('<em class="' + roomTabClass + '"></em>');
        }

        Candy.View.Event.Roster.onUpdate = function(vars) {
            var roomJid = vars['roomJid'];
            var userNick = vars['user']['data']['nick'];
            var userJid = vars['user']['data']['jid'];

            var userObject = $('#chat-rooms .room-pane[data-roomjid="' + roomJid + '"] .roster-pane .user[data-jid="' + userJid + '"]');

            if ($(userObject).hasClass('me')) {
                $(userObject).find('.label').html('<em class="icon-flag"></em> ' + userNick);
                $('#chat-rooms .room-pane[data-roomjid="' + roomJid + '"] .roster-pane').prepend($(userObject));
            }
        }
    };
    return self;

}(CandyShop.Class2Go || {}, Candy, jQuery));
