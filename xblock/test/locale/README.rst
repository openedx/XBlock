To generate the test translation file
=====================================

From the top-level "XBlock" directory:

1. Create a virtualenv.

2. pip install -r requirements/dev.txt

3. django-admin.py makemessages --settings xblock.test.settings -l de

4. Translate the required strings in the generated PO file.

5. django-admin.py compilemessages --settings xblock.test.settings -l de
