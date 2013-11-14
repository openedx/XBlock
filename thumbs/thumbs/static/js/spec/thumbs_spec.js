describe("Thumbs XBlock", function() {

    var thumbs;
    var mockRuntime;
    var element;

    beforeEach(function() {

        // Install the HTML fixture for this test
        setFixtures('<div id="fixture">\n' +
                    '<span class="upvote"><span class="count">NOT UPDATED</span></span>\n' +
                    '<span class="downvote"><span class="count">NOT UPDATED</span></span>\n' +
                    '</div>');

        // Create a mock for the runtime
        mockRuntime = jasmine.createSpyObj('runtime', ['handlerUrl']);
        mockRuntime.handlerUrl.andCallFake(function() {
            return 'test url';
        });

        // Intercept POST requests through JQuery
        spyOn($, 'ajax').andCallFake(function(params) {
            // Call through to the success handler
            params.success({up:'test up', down:'test down'});
        });

        // Load the HTML fixture defined in the test runner
        element = $('#fixture').get();

        // Run the ThumbsBlock script
        ThumbsBlock(mockRuntime, element);
    });

    it("upvotes on click", function() {
        // Click the upvote <span>
        $('#fixture .upvote').click();

        // Expect that the XBlock is updated via HTTP POST request
        expect($.ajax).toHaveBeenCalled();

        // Expect that the HTML gets updated
        actual = $('#fixture .upvote .count').text();
        expect(actual).toEqual('test up');
    });

    it("downvotes on click", function() {
        // Click the downvote <span>
        $('#fixture .downvote').click();

        // Expect that the XBlock is updated via HTTP POST request
        expect($.ajax).toHaveBeenCalled();

        // Expect that the HTML gets updated
        actual = $('#fixture .downvote .count').text();
        expect(actual).toEqual('test down');
    });
});
