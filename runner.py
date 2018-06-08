import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'xblock.test.settings'

from django.conf import settings
settings.configure(
    DEBUG=True,
    ALLOWED_HOSTS='*'
)

import django
django.setup()

# Now we instantiate a test runner...
from django.test.utils import get_runner
TestRunner = get_runner(settings)

# And then we run tests and return the results.
test_runner = TestRunner(verbosity=2, interactive=True)
failures = test_runner.run_tests(['xblock.test.django.test_field_translation'])
sys.exit(failures)
