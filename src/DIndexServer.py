#!/usr/bin/python

import socket
import time
import threading
import json
import argparse
import sys
from Queue import Queue

def get_args():
    """
    Get command line args from the user.
    """
    parser = argparse.ArgumentParser(
        description='Standard Arguments for talking to Distributed Index Server')
    parser.add_argument('-c', '--config',
                        required=True,
                        action='store',
                        help='Config file of the network')
    parser.add_argument('-s', '--server',
                        type=int,
                        required=True,
                        action='store',
                        help='Server Port Number')
    args = parser.parse_args()
    return args

class DIndexServer():
    def __init__(self, config, server_port, index=1, end=1):
        """
        Constructor used to initialize class object.

        @param config:         Network configuration.
        @param server_port:    Server Port.
        """
        self.peer_hostname = socket.gethostbyname(socket.gethostname())
        self.config = config
        self.mod_function = len(config['servers'])
        self.key_start = index
        self.key_end = end
        self.server_port = server_port
        self.hash_table = {}
        self.replica_hash_table = {}
        self.hash_table_replica_cmp = {}
        self.listener_queue = Queue()

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

    def _server_listener(self):
        """
        Server Listener Method is used start Distributed Index Server to listen on
        port: args.server_port for incoming connections.
        """
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            server_socket.bind((self.peer_hostname, self.server_port))
            server_socket.listen(10)
            while True:
                conn, addr = server_socket.accept()
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.listener_queue.put((conn,addr))
                threading.Thread(target=self._conn_operation).start()
        except Exception as e:
            print "Server Listener on port Failed: %s" % e
            sys.exit(1)

    def _put(self, conn, data_received):
        """
        This method is invoked by the peer trying to put key and value
        with the Indexing Server.

        @param conn:               Connection object from peer.
        @param data_received:      Data sent by the peer.

        @return boolean:           Success/Failure.
        """
        try:
            if self.hash_table.has_key(data_received['key']):
                self.hash_table[data_received['key']].append(data_received['value'])
            else:
                self.hash_table[data_received['key']] = [data_received['value']]
            print "Put Key: \'%s\' successfull, Hash Index: %s on Port: %s" % \
                  (data_received['key'], self.hash_index, self.server_port)
            conn.send(json.dumps(True))
        except Exception as e:
            print "Put Key: \'%s\' unsuccessfull, Hash Index: %s on Port: %s" % \
                  (data_received['key'], self.hash_index, self.server_port)
            print "DIndex Server Put function failure: %s" % e
            conn.send(json.dumps(False))

    def _replica_put(self, conn, data_received):
        """
        This method is invoked by the peer trying to replicate key and value
        with the Indexing Server.

        @param conn:               Connection object from peer.
        @param data_received:      Data sent by the peer.

        @return boolean:           Success/Failure.
        """
        try:
            if self.replica_hash_table.has_key(data_received['key']):
                self.replica_hash_table[data_received['key']].append(data_received['value'])
            else:
                self.replica_hash_table[data_received['key']] = [data_received['value']]
            print "Resilience Put Key: \'%s\' successfull, Hash Index: %s on Port: %s" % \
                  (data_received['key'], self.hash_index, self.server_port)
            conn.send(json.dumps(True))
        except Exception as e:
            print "Resilience Put Key: \'%s\' unsuccessfull, Hash Index: %s on Port: %s" % \
                  (data_received['key'], self.hash_index, self.server_port)
            print "DIndex Server Put Replica function failure: %s" % e
            conn.send(json.dumps(False))

    def _get(self, conn, data_received):
        """
        This method is invoked by the peer trying to get the value
        of the key present in the Indexing Server.

        @param conn:               Connection object from peer.
        @param data_received:      Data sent by the peer.

        @return value/boolean:     Value of the key/Failure.
        """
        try:
            if self.hash_table.has_key(data_received['key']):
                value = self.hash_table[data_received['key']]
                print "Get Key: \'%s\' Value: %s successfull, Hash Index: %s on Port: %s" % \
                      (data_received['key'],value,self.hash_index, self.server_port)
                conn.send(json.dumps(value))
            else:
                print "Get Value of Key: \'%s\' unsuccessfull, Hash Index: %s on Port: %s" % \
                      (data_received['key'],self.hash_index, self.server_port)
                conn.send(json.dumps(False))
        except Exception as e:
            print "DIndex Server Get function failure: %s" % e
            conn.send(json.dumps(False))

    def _replica_get(self, conn, data_received):
        """
        This method is invoked by the peer trying to get replica value
        of the key present in the Indexing Server.

        @param conn:               Connection object from peer.
        @param data_received:      Data sent by the peer.

        @return value/boolean:     Value of the key/Failure.
        """
        try:
            if self.replica_hash_table.has_key(data_received['key']):
                value = self.replica_hash_table[data_received['key']]
                print "Replica Get Key: \'%s\' Value: %s successfull, Hash Index: %s on Port: %s" % \
                      (data_received['key'],value,self.hash_index, self.server_port)
                conn.send(json.dumps(value))
                return
            print "Replica Get Value of Key: \'%s\' unsuccessfull, Hash Index: %s on Port: %s" % \
                  (data_received['key'],self.hash_index, self.server_port)
            conn.send(json.dumps(False))
        except Exception as e:
            print "DIndex Server Get Replica function failure: %s" % e
            conn.send(json.dumps(False))

    def _delete(self, conn, data_received):
        """
        This method is invoked by the peer trying to delete the key
        and value present in the Indexing Server.

        @param conn:               Connection object from peer.
        @param data_received:      Data sent by the peer.

        @return value/boolean:     Value of the key/Failure.
        """
        try:
            if not self.hash_table.has_key(data_received['key']):
                print "Delete Key: \'%s\' unsuccessfull, Hash Index: %s on Port: %s" % \
                      (data_received['key'],self.hash_index, self.server_port)
                conn.send(json.dumps(False))
                return
            self.hash_table.pop(data_received['key'], None)
            if self.hash_table_replica_cmp.has_key(data_received['key']):
                self.hash_table_replica_cmp.pop(data_received['key'], None)
            print "Delete Key: \'%s\' successfull, Hash Index: %s on Port: %s" % \
                  (data_received['key'],self.hash_index, self.server_port)
            conn.send(json.dumps(True))
        except Exception as e:
            print "DIndex Server Delete function failure: %s" % e
            conn.send(json.dumps(False))

    def _replica_delete(self, conn, data_received):
        """
        This method is invoked by the peer trying to delete replica value
        of the key present in the Indexing Server.

        @param conn:               Connection object from peer.
        @param data_received:      Data sent by the peer.

        @return value/boolean:     Value of the key/Failure.
        """
        try:
            if not self.replica_hash_table.has_key(data_received['key']):
                print "Replica Delete Key: \'%s\' unsuccessfull, Hash Index: %s on Port: %s" % \
                      (data_received['key'],self.hash_index, self.server_port)
                conn.send(json.dumps(False))
                return
            self.replica_hash_table.pop(data_received['key'], None)
            print "Replica Delete Key: \'%s\' successfull, Hash Index: %s on Port: %s" % \
                  (data_received['key'],self.hash_index, self.server_port)
            conn.send(json.dumps(True))
        except Exception as e:
            print "DIndex Server Delete Replica function failure: %s" % e
            conn.send(json.dumps(False))

    def _resilience_put(self, key, value):
        """
        This method is used to ensure data resilience of put function

        @param key:        key to be sent to server.
        @param value:      Value to be sent to server.
        """
        try:
            cmd_issue = {
                'command' : 'replica_put',
                'key' : key,
                'value' : value
            }

            self.server_to_server_socket.sendall(json.dumps(cmd_issue))
            rcv_data = json.loads(self.server_to_server_socket.recv(1024))
            if rcv_data:
                if self.hash_table_replica_cmp.has_key(key):
                    self.hash_table_replica_cmp[key].append(value)
                else:
                    self.hash_table_replica_cmp[key] = [value]
        except Exception as e:
            print "Resilience Put Error, %s" % e

    def _data_resilience(self):
        """
        This method is used to ensure data resilience system wide.
        """
        try:
            while True:
                if self.hash_table:
                    for key,value in self.hash_table.iteritems():
                        if self.hash_table_replica_cmp.has_key(key):
                            replica_values = self.hash_table_replica_cmp[key]
                            update_values = list(set(value) - set(replica_values))
                            for v in update_values:
                                self._resilience_put(key, v)
                        else:
                            for v in value:
                                self._resilience_put(key, v)
                    time.sleep(5)
                else:
                    time.sleep(10)
        except Exception as e:
            print "Data Resilience Error, %s" % e

    def _conn_operation(self):
        """
        Starting thread to carry out server operations.
        """
        try:
            conn, addr = self.listener_queue.get()
            if conn:
                while True:
                    data_received = json.loads(conn.recv(1024))
                    print "Got connection from %s on port %s, requesting " \
                          "for: %s" % (addr[0], addr[1], data_received['command'])

                    if data_received['command'] == 'put':
                        self._put(conn, data_received)
                    elif data_received['command'] == 'get':
                        self._get(conn, data_received)
                    elif data_received['command'] == 'delete':
                        self._delete(conn, data_received)
                    elif data_received['command'] == 'replica_put':
                        self._replica_put(conn, data_received)
                    elif data_received['command'] == 'replica_get':
                        self._replica_get(conn, data_received)
                    elif data_received['command'] == 'replica_delete':
                        self._replica_delete(conn, data_received)
                    elif data_received['command'] == 'close':
                        conn.close()
                        break

                    print "hash table: || %s" % \
                          self.hash_table
                    print "Replica hash table: || %s" % \
                          self.replica_hash_table
        except ValueError as e:
            pass
        except Exception as e:
            self.server_to_server_socket.close()
            print "Server Operations error, %s " % e
            sys.exit(1)

    def start_server(self):
        """
        This method is used to start the Distributed Index Server.
        """
        try:
            print "Starting Distributed Indexing Server with",
            for i in range (0,len(self.config['servers'])):
                if self.config['servers'][i]['port'] == self.server_port:
                    print "Hash Index: %s on Port: %s" % (i,self.server_port)
                    self.hash_index = i
            if self.hash_index == len(self.config['servers']) - 1:
                self.replica_index = 0
            else:
                self.replica_index = self.hash_index + 1

            print "Starting Distributed Indexing Server Listener...",
            listener_thread = threading.Thread(target=self._server_listener)
            listener_thread.setDaemon(True)
            listener_thread.start()
            dr_thread = threading.Thread(target=self._data_resilience)
            dr_thread.setDaemon(True)
            dr_thread.start()
            print "Done!"
            time.sleep(10)
            self.server_to_server_socket = \
                socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_to_server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_to_server_socket.setsockopt(
                    socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.server_to_server_socket.connect(
                        (self.config['servers'][self.replica_index]['ip'],
                         self.config['servers'][self.replica_index]['port']))
            listener_thread.join()
        except Exception as e:
            print "Distributed Index Server error: %s" % e
            sys.exit(1)

if __name__ == '__main__':
    """
    Main method to start Distributed Hash Table.
    """
    try:
        args = get_args()
        with open(args.config) as f:
            config = json.loads(f.read())

        server = DIndexServer(config, args.server)
        server.start_server()
    except Exception as e:
        print "main function error: %s" % e
        sys.exit(1)
    except (KeyboardInterrupt, SystemExit):
        print "Distributed Index Server Shutting down..."
        time.sleep(1)
        sys.exit(1)

__author__ = 'arihant'
