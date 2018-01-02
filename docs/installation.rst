.. highlight:: shell

============
Installation
============


Stable release
--------------

To install collectd-qdrouterd, run this command in your terminal:

.. code-block:: console

    $ pip install collectd-qdrouterd

This is the preferred method to install collectd-qdrouterd, as it will always install the most recent stable release. 

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for collectd-qdrouterd can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/ajssmith/collectd-qdrouterd

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/ajssmith/collectd-qdrouterd/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/ajssmith/collectd-qdrouterd
.. _tarball: https://github.com/ajssmith/collectd-qdrouterd/tarball/master

This plugins requires that the Collectd type database be updated. Each of these statistics have their own custom enter in collectd's type database. To add these types defined in :download:`this example <../config/types.db.custom>` run the following command::

    $ cat config/types.db.custom >> /usr/share/collectd/types.db
