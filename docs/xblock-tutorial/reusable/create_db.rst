**************************
Create the SQLite Database
**************************

Before running the XBlock SDK the first time, you must create the SQLite
database.

#. In the ``xblock_development`` directory, run the following command to create
   the database and the tables.

   .. code-block:: none

      (venv) $ python xblock-sdk/manage.py migrate

#. You are prompted to indicate whether or not to create a Django superuser.

   .. code-block:: none

      You just installed Django's auth system, which means you don't have any
      superusers defined. Would you like to create one now? (yes/no):

#. Enter ``no``.
