#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
This module retrieves qdrouterd metrics to provide to collectd
"""

import collectd
import re

from collectd_qdrouterd.qdrouterd import QdrouterdClient

CONFIGS = []
INSTANCES = []

def configure(config_values):
    """
    Converts a collectd configuration into qdrouterd configuration.
    """

    collectd.debug('Configuring Qdrouterd Plugin')
    link_include = list()
    addr_include = list()

    for config_value  in config_values.children:
        if config_value.key == 'Host':
            host = config_value.values[0]
        elif config_value.key == 'Port':
            port = config_value.values[0]
        elif config_value.key == 'Username':
            username = config_value.values[0]
        elif config_value.key == 'Password':
            password = config_value.values[0]
        elif config_value.key == 'Router':
            router = config_value.values[0]
        elif config_value.key == 'Links':
            links = config_value.values[0]
        elif config_value.key == 'Addresses':
            addr = config_value.values[0]
        elif config_value.key == 'Memory':
            mem = config_value.values[0]
        elif config_value.key == 'LinkInclude':
            for pattern in config_value.children:
                link_include.append(pattern.values[0])
        elif config_value.key == 'AddressInclude':
            for pattern in config_value.children:
                addr_include.append(pattern.values[0])
        else:
            collectd.warning('qdrouterd plugin: unknown config key: %s', config_value.key)

    global CONFIGS

    config = QdrouterdConfig(host, port, username, password,
                             router, links, addr, mem,
                             link_include, addr_include)
    CONFIGS.append(config)


def read():
    """
    Retrieve metrics and dispatch data.
    """
    collectd.debug('Reading data from qdrouterd and dispatching')
    for config in CONFIGS:
        INSTANCES.append(CollectdPlugin(config))
    for instance in INSTANCES:
        instance.read()
    for instance in INSTANCES:
        instance.close()
    INSTANCES.clear()

def shutdown():
    """
    Terminate data connections.
    """
    collectd.debug('Shutting down connections to qdrouterd')
    for instance in INSTANCES:
        instance.close()

class QdrouterdConfig(object):
    """
    Class that contains the qdrouterd plugin configuration
    """

    def __init__(self, host, port, username, password,
                 router, links, addr, mem,
                 link_include=None, addr_include=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.router = router
        self.links = links
        self.addr = addr
        self.mem = mem
        self.link_include = list()
        self.addr_include = list()
        if link_include:
            for pattern in link_include:
                self.link_include.append(re.compile(pattern))
        if addr_include:
            for pattern in addr_include:
                self.addr_include.append(re.compile(pattern))

    def is_link_included(self, name):
        if len(self.link_include) > 0:
            for pattern in self.link_include:
                search = pattern.search(name)
                if search:
                    return True
            return False
        return True

    def is_addr_included(self, name):
        if len(self.addr_include) > 0:
            for pattern in self.addr_include:
                search = pattern.search(name)
                if search:
                    return True
            return False
        return True


CAPS_RE = re.compile('[A-Z]')

def uncamelcase(str, separator='-'):
    """Convert camelCase string str to string with separator, e.g. camel_case"""
    if len(str) == 0: return str
    return str[0] + CAPS_RE.sub(lambda m: separator+m.group(0).lower(), str[1:])

class CollectdPlugin(QdrouterdClient):
    """
    Manages interaction between qdrouterd stats and collectd
    """
    router_stats = ('linkRouteCount', 'autoLinkCount', 'linkCount',
                    'nodeCount', 'addrCount', 'connectionCount',
                    'id')
    link_stats = ('undeliveredCount', 'unsettledCount', 'deliveryCount',
                  'presettledCount', 'acceptedCount', 'rejectedCount',
                  'releasedCount', 'modifiedCount', 'linkName')
    addr_stats = ('inProcess', 'subscriberCount', 'remoteCount',
                  'containerCount', 'deliveriesIngress', 'deliveriesEgress',
                  'deliveriesTransit', 'deliveriesToContainer',
                  'deliveriesFromContainer', 'name')
    mem_stats = ('localFreeListMax', 'totalAllocFromHeap', 'heldByThreads', 
                 'batchesRebalancedToThreads', 'batchesRebalancedToGlobal',
                 'identity')
    
    def __init__(self,config):
        self.config = config
        self.url = "amqp://" + config.host + ":" + config.port
        super(CollectdPlugin, self).__init__(
            QdrouterdClient.connection(self.url))


    def _addr_text(self, addr):
        if not addr:
            return ""
        if addr[0] == 'M':
            return addr[2:]
        else:
            return addr[1:]


    def _identity_clean(self, identity, router_id=None):
        if router_id:
            return router_id
        if not identity:
            return "-"
        pos = identity.find('/')
        if pos >= 0:
            return identity[pos + 1:]
        return identity


    def query(self, entity_type, attribute_names=None, limit=None):
        return super(CollectdPlugin, self).query(entity_type, attribute_names, count=limit).get_entities()


    def read(self):
        """
        Dispatches metric values to collectd.
        """
        if self.config.router:
            self.dispatch_router()
        if self.config.links:
            self.dispatch_links()
        if self.config.addr:
            self.dispatch_addresses()
        if self.config.mem:
            self.dispatch_memory()


    def dispatch_router(self):
        """
        Dispatch general router data
        """
        collectd.debug('Dispatching general router data')

        objects = self.query('org.apache.qpid.dispatch.router')

        router = objects[0]
        for stat_name in self.router_stats:
            if stat_name != 'id':
                value = str(getattr(router, stat_name))
                self.dispatch_values(value,
                                     self.config.host,
                                     'router',
                                     router.id,
                                     uncamelcase(stat_name))


    def dispatch_links(self):
        """
        Dispatch link data
        """
        collectd.debug('Dispatching link data')

        objects = self.query('org.apache.qpid.dispatch.router.link')

        for link in objects:
            if not self.config.is_link_included(link.linkName):
                continue
            for stat_name in self.link_stats:
                if stat_name != 'linkName':
                    value = str(getattr(link, stat_name))
                    self.dispatch_values(value,
                                         self.config.host,
                                         'link',
                                         link.linkName,
                                         uncamelcase(stat_name))


    def dispatch_addresses(self):
        """
        Dispatch address data
        """
        collectd.debug('Dispatching address data')
        
        objects = self.query('org.apache.qpid.dispatch.router.address')

        for addr in objects:
            if not self.config.is_addr_included(addr.name):
                continue
            for stat_name in self.addr_stats:
                if stat_name != 'name':
                    value = str(getattr(addr, stat_name))
                    self.dispatch_values(value,
                                         self.config.host,
                                         'address',
                                         self._addr_text(addr.name),
                                         uncamelcase(stat_name))

            
    def dispatch_memory(self):
        """
        Dispatch memory data
        """
        collectd.debug('Dispatching memory data')
        
        objects = self.query('org.apache.qpid.dispatch.allocator')

        for mem in objects:
            for stat_name in self.mem_stats:
                if stat_name != 'identity':
                    value = str(getattr(mem, stat_name))
                    self.dispatch_values(value,
                                         self.config.host,
                                         'memory',
                                         mem.identity,
                                         uncamelcase(stat_name))



    @staticmethod                                 
    def dispatch_values(values, host, plugin, plugin_instance,
                        metric_type, type_instance=None):
        """
        Dispatch metrics to collectd.
        """
        path = "{0}.{1}.{2}.{3}.{4}".format(host,
                                            plugin,
                                            plugin_instance,
                                            metric_type,
                                            type_instance)
        try:
            val = collectd.Values()
            val.host = host

            val.plugin = plugin

            if plugin_instance:
                val.plugin_instance = plugin_instance

            val.type = metric_type

            if type_instance:
                val.type_instance = type_instance

            val.values = [values]

            val.dispatch()
        except Exception as ex:
            collectd.warning("Failed to dispatch %s. Exception %s" %
                             (path, ex))

#
# Register callbacks to collectd
#
collectd.register_config(configure)
collectd.register_read(read)
collectd.register_shutdown(shutdown)
