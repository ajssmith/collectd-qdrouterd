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

def configure(config):
    """
    Converts a collectd configuration into qdrouterd configuration.
    """

    collectd.debug('Configuring Qdrouterd Plugin')

    for node in config.children:
        key = node.key.lower()
        val = node.values[0]

        if key == 'host':
            host = val
        elif key == 'port':
            port = val
        elif key == 'username':
            username = val
        elif key == 'password':
            password = val
        elif key == 'router':
            router = val
        elif key == 'links':
            links = val
        elif key == 'addresses':
            addr = val
        elif key == 'memory':
            mem = val
        else:
            collectd.warning('qdrouterd plugin: unknown config key: %s', key)

    global CONFIGS

    CONFIGS.append({'host': host, 'port': port, 'username': username, 'password': password,
                    'router': router, 'links': links, 'addr': addr, 'mem': mem})
    
    
def init():
    """
    Create the plugin object
    """
    for config in CONFIGS:
        INSTANCES.append(CollectdPlugin(config))


def read():
    """
    Retrieve metrics and dispatch data.
    """
    collectd.debug('Reading data from qdrouterd and dispatching')
    if not INSTANCES:
        collectd.warning('Qdrouterd plugin not ready')
        return
    for instance in INSTANCES:
        instance.read()


def shutdown():
    """
    Terminate data connections.
    """
    collectd.debug('Shutting down connections to qdrouterd')
    for instance in INSTANCES:
        instance.close()


def get(obj, attr):
    if attr in obj.__dict__:
        return obj.__dict__[attr]
    return None

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
        self.url = "amqp://" + config['host'] + ":" + config['port']
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
        if attribute_names:
            unames = []
            for a in attribute_names:
                unames.append(a)
            attribute_names = unames
        return super(CollectdPlugin, self).query(entity_type, attribute_names, count=limit).get_entities()


    def read(self):
        """
        Dispatches metric values to collectd.
        """
        if self.config['router']:
            self.dispatch_router()
        if self.config['links']:
            self.dispatch_links()
        if self.config['addr']:
            self.dispatch_addresses()
        if self.config['mem']:
            self.dispatch_memory()


    def dispatch_router(self):
        """
        Dispatch general router data
        """
        collectd.debug('Dispatching general router data')

        objects = self.query('org.apache.qpid.dispatch.router',
                             self.router_stats)

        router = objects[0]
        for stat_name in self.router_stats:
            if stat_name != 'id':
                value = str(get(router, stat_name))
                self.dispatch_values(value,
                                     self.config['host'],
                                     'router',
                                     router.id,
                                     uncamelcase(stat_name))


    def dispatch_links(self):
        """
        Dispatch link data
        """
        collectd.debug('Dispatching link data')
        
        objects = self.query('org.apache.qpid.dispatch.router.link',
                             self.link_stats)

        for link in objects:
            for stat_name in self.link_stats:
                if stat_name != 'linkName':
                    value = str(get(link, stat_name))
                    self.dispatch_values(value,
                                         self.config['host'],
                                         'link',
                                         link.linkName,
                                         uncamelcase(stat_name))

                   
    def dispatch_addresses(self):
        """
        Dispatch address data
        """
        collectd.debug('Dispatching address data')
        
        objects = self.query('org.apache.qpid.dispatch.router.address',
                             self.addr_stats)

        for addr in objects:
            for stat_name in self.addr_stats:
                if stat_name != 'name':
                    value = str(get(addr, stat_name))
                    self.dispatch_values(value,
                                         self.config['host'],
                                         'address',
                                         self._addr_text(addr.name),
                                         uncamelcase(stat_name))

            
    def dispatch_memory(self):
        """
        Dispatch memory data
        """
        collectd.debug('Dispatching memory data')
        
        objects = self.query('org.apache.qpid.dispatch.allocator',
                             self.mem_stats)

        for mem in objects:
            for stat_name in self.mem_stats:
                if stat_name != 'identity':
                    value = str(get(mem, stat_name))
                    self.dispatch_values(value,
                                         self.config['host'],
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
collectd.register_init(init)
collectd.register_read(read)
collectd.register_shutdown(shutdown)
