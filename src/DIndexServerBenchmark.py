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
        self.listener_queue = Queue()
        self.server_sockets = []

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
            conn.send(json.dumps(True))
        except Exception as e:
            print "DIndex Server put function failure: %s" % e
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
                conn.send(json.dumps(self.hash_table[data_received['key']]))
            else:
                conn.send(json.dumps(False))
        except Exception as e:
            print "DIndex Server Get function failure: %s" % e
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
                conn.send(json.dumps(False))
                return
            self.hash_table.pop(data_received['key'], None)
            conn.send(json.dumps(True))
        except Exception as e:
            print "DIndex Server Delete function failure: %s" % e
            conn.send(json.dumps(False))

    def _conn_operation(self):
        """
        Starting thread to carry out server operations.
        """
        try:
            conn, addr = self.listener_queue.get()
            if conn:
                while True:
                    data_received = json.loads(conn.recv(1024))
                    if data_received['command'] == 'put':
                        self._put(conn, data_received)
                    elif data_received['command'] == 'get':
                        self._get(conn, data_received)
                    elif data_received['command'] == 'delete':
                        self._delete(conn, data_received)
                    elif data_received['command'] == 'close':
                        conn.close()
                        break
        except Exception as e:
            print "connection operation error: %s" % e

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

            print "Starting Distributed Indexing Server Listener...",
            self.listener_thread = threading.Thread(target=self._server_listener)
            self.listener_thread.setDaemon(True)
            self.listener_thread.start()
            print "Done!"
            self.listener_thread.join()
        except Exception as e:
            print "Distributed Index Server error: %s" % e
            print "Distributed Index Server Shutting down..."
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
