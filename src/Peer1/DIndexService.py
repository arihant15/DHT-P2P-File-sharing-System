#!/usr/bin/python

import socket
import json
import time

class DIndexService():
    def __init__(self, config, index=1, end=1):
        """
        Constructor used to initialize class object.
        """
        self.peer_hostname = socket.gethostbyname(socket.gethostname())
        self.config = config
        self.mod_function = len(config['servers'])
        self.key_start = index
        self.key_end = end
        self.server_sockets = []

    def _hash_function(self, key):
        """
        hash_function method is used to return the server location for
        storage/retrieval of key,value based on the hash function calculation.

        @param key:    The value stored as key in distributed index server.
        """
        try:
            h = hash(key)
            index = h % self.mod_function
            return index
        except Exception as e:
            print "hash function error: %s" % e

    def establish_connection(self):
        """
        Establish socket connection with DHT servers.
        """
        try:
            for i in range(0,len(self.config['servers'])):
                timeout = 0
                while timeout < 60:
                    try:
                        s = \
                            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.setsockopt(
                            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        s.setsockopt(
                            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        s.connect(
                                (self.config['servers'][i]['ip'],
                                 self.config['servers'][i]['port']))
                        self.server_sockets.append(s)
                        break
                    except Exception as e:
                        time.sleep(10)
                        timeout = timeout + 10
        except Exception as e:
            print "Establish Connection Error: %s" % e

    def disable_connection(self):
        """
        Disable socket connection with DHT servers.
        """
        try:
            for s in self.server_sockets:
                cmd_issue = {
                    'command' : 'close'
                }
                try:
                    s.sendall(json.dumps(cmd_issue))
                    s.close()
                except Exception as e:
                    pass
        except Exception as e:
            print "Disable Connection Error: %s" % e
    
    def put(self, key, value):
        """
        Put method is used to store the key and value in the
        distributed index server.

        @param key:     Key to be stored in the Index Server.
        @param value:   Value to be stored in the Index Server.
        """
        try:
            cmd_issue = {
                'command' : 'put',
                'key' : key,
                'value' : value,
                'pad' : ''
            }
            padding = 1024 - len(json.dumps(cmd_issue))
            cmd_issue['pad'] = '*' * padding
            index = self._hash_function(key)
            server = self.config['servers'][index]
            try:
                self.server_sockets[index].sendall(json.dumps(cmd_issue))
                rcv_data = json.loads(self.server_sockets[index].recv(1024))
                if not rcv_data:
                    raise Exception
            except Exception as e:
                if index == len(self.config['servers']) - 1:
                    index = 0
                else:
                    index = index + 1
                server = self.config['servers'][index]
                cmd_issue = {
                    'command' : 'replica_put',
                    'key' : key,
                    'value' : value,
                    'pad' : ''
                }
                padding = 1024 - len(json.dumps(cmd_issue))
                cmd_issue['pad'] = '*' * padding
                try:
                    self.server_sockets[index].sendall(json.dumps(cmd_issue))
                    rcv_data = json.loads(self.server_sockets[index].recv(1024))
                except Exception as e:
                    rcv_data = None
            return rcv_data
        except Exception as e:
            print "Put function error: %s" % e
            return None

    def get(self, key):
        """
        Get method is used to retrieve the value from the
        distributed index server.

        @param key:    the key whose value needs to be retrieved.
        """
        try:
            cmd_issue = {
                'command' : 'get',
                'key' : key,
                'pad' : ''
                }
            padding = 1024 - len(json.dumps(cmd_issue))
            cmd_issue['pad'] = '*' * padding
            index = self._hash_function(key)
            server = self.config['servers'][index]
            try:
                self.server_sockets[index].sendall(json.dumps(cmd_issue))
                rcv_data = json.loads(self.server_sockets[index].recv(1024))
                if not rcv_data:
                    raise Exception
            except Exception as e:
                if index == len(self.config['servers']) - 1:
                    index = 0
                else:
                    index = index + 1
                server = self.config['servers'][index]
                cmd_issue = {
                    'command' : 'replica_get',
                    'key' : key,
                    'pad' : ''
                    }
                padding = 1024 - len(json.dumps(cmd_issue))
                cmd_issue['pad'] = '*' * padding
                try:
                    self.server_sockets[index].sendall(json.dumps(cmd_issue))
                    rcv_data = json.loads(self.server_sockets[index].recv(1024))
                except Exception as e:
                    rcv_data = None
            return rcv_data
        except Exception as e:
            print "Get function error: %s" % e
            return None

    def delete(self, key):
        """
        delete method is used to delete the key and value from the
        distributed index server.

        @param key:    the key whose entree needs to be deleted.
        """
        try:
            index = self._hash_function(key)
            server = self.config['servers'][index]
            cmd_issue = {
                'command' : 'delete',
                'key' : key,
                'pad' : ''
                }
            padding = 1024 - len(json.dumps(cmd_issue))
            cmd_issue['pad'] = '*' * padding
            index = self._hash_function(key)
            try:
                self.server_sockets[index].sendall(json.dumps(cmd_issue))
                rcv_data = json.loads(self.server_sockets[index].recv(1024))
                raise Exception
            except Exception as e:
                if index == len(self.config['servers']) - 1:
                    index = 0
                else:
                    index = index + 1
                cmd_issue = {
                    'command' : 'replica_delete',
                    'key' : key,
                    'pad' : ''
                }
                padding = 1024 - len(json.dumps(cmd_issue))
                cmd_issue['pad'] = '*' * padding
                try:
                    self.server_sockets[index].sendall(json.dumps(cmd_issue))
                    rcv_data = json.loads(self.server_sockets[index].recv(1024))
                except Exception as e:
                    rcv_data = None
            if rcv_data:
                print "Peer Delete Key: \'%s\' on server successful." % (key)
            else:
                print "Peer Delete Key: \'%s\' on server unsuccessful." % (key)

        except Exception as e:
            print "Delete function error: %s" % e

__author__ = 'arihant'
