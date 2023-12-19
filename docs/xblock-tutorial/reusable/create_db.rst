**************************
Create the SQLite Database
**************************

Before running the XBlock SDK the first time, you must create the SQLite
database.

#. In the ``xblock_development`` directory, run the following command to create
   the database and the tables.

   .. code-block:: none

      (xblock-env) $ python xblock-sdk/manage.py migrate

