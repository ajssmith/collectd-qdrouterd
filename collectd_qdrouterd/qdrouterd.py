#!/usr/bin/env python
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import collectd
import itertools, re

import proton
from proton import Message, Url, ConnectionException, Timeout, SSLDomain
from proton.utils import SyncRequestResponse, BlockingConnection

class Entity(object):
    """
    A collection of named attributes.
    """

    def __init__(self, attributes=None, **kwargs):
        self.__dict__['attributes'] = {}
        if attributes:
            for k, v in attributes.items():
                self.attributes[k] = v
                self.__dict__[self._pyname(k)] = v
        for k, v in kwargs.items():
            self._set(k, v)

    def __getitem__(self, name):
        return self.attributes[name]

    def __getattr__(self, name):
        return self.attributes[name]

    def __contains__(self, name):
        return name in self.attributes

    @staticmethod
    def _pyname(name): return name.replace('-', '_')

    def __repr__(self): return "Entity(%r)" % self.attributes
        
class QdrouterdClient(object):
    """
    Class to interface with the Qdrouterd AMQP 1.0 API
    """
    @staticmethod
    def connection(url=None, timeout=10, ssl_domain=None, sasl=None):
        """
        Return a BlockingConnection for connection to a managemenet node
        """
        url = Url(url)

        url.path = u'$management'

        if ssl_domain:
            sasl_enabled = True
        else:
            sasl_enabled = True if sasl else False

        return BlockingConnection(url,
                                  timeout=timeout,
                                  ssl_domain=ssl_domain,
                                  sasl_enabled=sasl_enabled,
                                  allowed_mechs=str(sasl.mechs) if sasl and sasl.mechs != None else None,
                                  user=str(sasl.user) if sasl else None,
                                  password=str(sasl.password) if sasl else None)

    @staticmethod
    def connect(url=None, timeout=10, ssl_domain=None, sasl=None):
        """
        Return a Node connected with the given parameters, see L{connection}
        """
        return QdrouterdClient(QdrouterdClient.connection(url, timeout, ssl_domain, sasl))      
        
    def __init__(self, connection):
        """
        Create a management client proxy using the given connection.
        """
        self.name = self.identity = u'self'
        self.type = u'org.amqp.management' # AMQP management node type
        self.url = connection.url
        self.client = SyncRequestResponse(connection, self.url.path)
        self.reply_to = self.client.reply_to

    def close(self):
        """
        Shut down the client
        """
        if self.client:
            self.client.connection.close()
            self.client = None

    def __repr__(self):
        return "%s(%s)"%(self.__class__.__name__, self.url)

    def request(self, body=None, **properties):
        """
        Make a L{proton.Message} containining a management request.
        """
        request = proton.Message()
        request.properties = properties
        request.body = body or {}
        return request

    def client_request(self, body=None, **properties):
        """
        Construct a request 
        """
        return self.request(body, name=self.name, type=self.type, **properties)

    def call(self, request):
        """
        Send a management request message, wait for a response.
        """
        response = self.client.call(request)
        return response

    class QueryResponse(object):
        """
        Result returned by L{query}.
        """
        def __init__(self, qdrouterd_client, attribute_names, results):
            """
            @param response: the respose message to a query.
            """
            self.qdrouterd_client = qdrouterd_client
            self.attribute_names = attribute_names
            self.results = results

        def iter_dicts(self, clean=False):
            """
            Return an iterator that yields a dictionary for each result.
            """
            for r in self.results:
                if clean: yield clean_dict(zip(self.attribute_names, r))
                else: yield dict(zip(self.attribute_names, r))

        def iter_entities(self, clean=False):
            """
            Return an iterator that yields an L{Entity} for each result.
            """
            for d in self.iter_dicts(clean=clean): yield Entity(d)
            
        def get_dicts(self, clean=False):
            """
            Results as list of dicts.
            """
            return [d for d in self.iter_dicts(clean=clean)]

        def get_entities(self, clean=False):
            """
            Results as list of entities.
            """
            return [d for d in self.iter_entities(clean=clean)]

        def __repr__(self):
            return "QueryResponse(attribute_names=%r, results=%r"%(self.attribute_names, self.results)

    def query(self, type=None, attribute_names=None, offset=None, count=None):
        """
        Send an AMQP management query message and return the response.
        At least one of type, attribute_names must be specified.
        """
        request = self.client_request(
            {u'attributeNames': attribute_names or []},
            operation=u'QUERY', entityType=type, offset=offset, count=count)

        response = self.call(request)
        return QdrouterdClient.QueryResponse(self, response.body[u'attributeNames'], response.body[u'results'])
