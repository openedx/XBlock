# JavaScript Testing

This is an example of how to use Jasmine to unit-test the
JavaScript used by the `thumbs` XBlock.

## Installing Jasmine

We use the Ruby gem version of Jasmine to run the tests.
To install the gem:

    gem install jasmine


## Directory Structure

* JavaScript files being tested are located in `public/javascripts`

* Tests (called "specs") are located in `spec/javascripts`

* HTML fixtures are located in `spec/javascripts/fixtures`

* Library dependencies (such as jquery) are located in `lib`


The directory structure was set up using the Jasmine gem.  You can
set up something similar in another directory using the command:

    jasmine init

See [jasmine-gem](http://github.com/pivotal/jasmine-gem) for more
information.


## Running the Tests

To run the tests, first run:

    rake jasmine

from this directory.

Then point your browser to `localhost:8888` to view test results.
