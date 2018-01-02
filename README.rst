==================
collectd-qdrouterd
==================


.. image:: https://img.shields.io/pypi/v/collectd-qdrouterd.svg
        :target: https://pypi.python.org/pypi/collectd-qdrouterd

.. image:: https://img.shields.io/travis/ajssmith/collectd-qdrouterd.svg
        :target: https://travis-ci.org/ajssmith/collectd-qdrouterd

.. image:: https://readthedocs.org/projects/collectd-qdrouterd/badge/?version=latest
        :target: https://collectd-qdrouterd.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/ajssmith/collectd-qdrouterd/shield.svg
     :target: https://pyup.io/repos/github/ajssmith/collectd-qdrouterd/
     :alt: Updates


"A collectd plugin, written in python, to collect statistics from Qpid Dispatch Router."


* Free software: Apache Software License 2.0
* Documentation: https://collectd-qdrouterd.readthedocs.io.


Features
--------

* Support router, link, address and memory stats
  
* TODO: tests, certs, possibly aggregates

Configuration
-------------

The plugin supports the following configuration options:

* `Host`: The hostname that the qdrouterd service is running on. Defaults to `localhost`
* `Port`: The network port that the qdrouterd service is listening on. Defaults to `5672`
* `Username`: The qdrouterd user. Defaults to `guest`
* `Password`: The qdrouterd user password. Defaults to `guest`
* `Router`: Indicator to dispatch general router stats. Defaults to `false`
* `Links`: Indicator to dispatch individual link stats. Defaults to `true`
* `Addresses`: Indicator to dispatch individual address stats. Defaults to `false`
* `Memory`: Indicator to dispatch memory profile stats. Defaults to `false`

See `this example`_ for further details.
    .. _this example: config/collectd.conf
    
Router
------

For each router server, the following statistics are gathered:

* link-route-count
* auto-link-count
* link-count
* node-count
* addr-count
* connection-count

Links
-----

For each operational link on a server, the following statistics are gathered:

* undelivered-count
* unsettled-count
* delivery-count
* presettled-count
* accepted-count
* rejected-count
* released-count
* modified-count

Addresses
---------

For each operational address on a server, the following statistics are gathered:

* in-process
* subscriber-count    
* remote-count
* container-count
* deliveries-ingress
* deliveries-egress
* deliveries-transit
* deliveries-to-container
* deliveries-from-container

Memory
------

For each memory type on a server, the following statistics are gathered:

* local-free-list-max
* total-alloc-from-heap
* held-by-threads
* batches-rebalanced-to-threads
* batches-rebalanced-to-global

Credits
-------

This package was created with Cookiecutter_ and the `cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

