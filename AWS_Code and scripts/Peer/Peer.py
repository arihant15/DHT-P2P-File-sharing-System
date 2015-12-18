#!/usr/bin/python

import socket
import time
import json
import os
import threading
import argparse
from DIndexService import DIndexService
import sys
sys.path.append('..')
from Queue import Queue
from concurrent import futures

SHARED_DIR = "./Active-Files"
HOST_IP = socket.gethostbyname(socket.gethostname())

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
    parser.add_argument('-p', '--port',
                        type=int,
                        required=True,
                        action='store',
                        help='Peer Server Port Number')
    parser.add_argument('-r', '--replica',
                        type=int,
                        default=1,
                        action='store',
                        help='Data Replication Factor')
    args = parser.parse_args()
    return args

class PeerOperations(threading.Thread):
    def __init__(self, threadid, name, p):
        """
        Constructor used to initialize class object.

        @param threadid:    Thread ID.
        @param name:        Name of the thread.
        @param p:           Class Peer Object.
        """
        threading.Thread.__init__(self)
        self.threadID = threadid
        self.name = name
        self.peer = p
        self.peer_server_listener_queue = Queue()

    def peer_server_listener(self):
        """
        Peer Server Listener Method is used by Peer Server to listen on
        port: assigned by Index Server for incoming connections.
        """
        try:
            peer_server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            peer_server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            peer_server_socket.setsockopt(
                socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            peer_server_host = self.peer.peer_hostname
            peer_server_port = self.peer.peer_port
            peer_server_socket.bind(
                (peer_server_host, peer_server_port))
            peer_server_socket.listen(10)
            while True:
                conn, addr = peer_server_socket.accept()
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                #print "Got connection from %s on port %s" \
                #          % (addr[0], addr[1])
                self.peer_server_listener_queue.put((conn,addr))
        except Exception as e:
            print "Peer Server Listener on port Failed: %s" % e
            sys.exit(1)

    def get_chunks(self,file_size):
        """
        get chunk function is used to determine the chunk size
        to send over the socket.

        @param file_size:        Size of the file
        @return chunk_size:      Size of chunk
        """
        chunk_start = 0
        chunk_size = 0xA00000  # 10485760 bytes, default max ssl buffer size
        while chunk_start + chunk_size <= file_size:
            yield(chunk_start, chunk_size)
            chunk_start += chunk_size
        final_chunk_size = file_size - chunk_start
        yield(chunk_start, final_chunk_size)

    def peer_server_upload(self, conn, data_received):
        """
        This method is used to enable file transfer between peers.

        @param conn:              Connection object.
        @param data_received:     Received data containing file name.
        """
        try:
            file_size = os.path.getsize(SHARED_DIR+'/'+data_received['file_name'])
            f = open(SHARED_DIR+'/'+data_received['file_name'], 'rb')
            #print "Hosting File: %s for download" % data_received
            for chunk_start, chunk_size in self.get_chunks(file_size):
                file_chunk = f.read(chunk_size)
                conn.sendall(file_chunk)
            f.close()
            conn.sendall('')
            conn.close()
        except Exception as e:
            conn.sendall(json.dumps(False))
            conn.close()
            print "File Upload Error, %s" % e

    def peer_replica_download(self, conn, data_received):
        """
        This method is used to enable replica file transfer between peers.

        @param conn:              Connection object.
        @param data_received:     Received data containing file name.
        """
        try:
            peer_replica_request_addr, peer_replica_request_port = \
                data_received['peer_id'].split(':')
            peer_replica_request_socket = \
                socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_replica_request_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            peer_replica_request_socket.connect(
                (peer_replica_request_addr, int(peer_replica_request_port)))

            cmd_issue = {
                'command' : 'obtain_active',
                'file_name' : data_received['file_name']
            }

            peer_replica_request_socket.sendall(json.dumps(cmd_issue))
            f = open(SHARED_DIR+'/'+data_received['file_name'], 'wb')
            while True:
                data = peer_replica_request_socket.recv(10485760)
                if data:
                    f.write(data)
                else:
                    f.close()
                    break
            peer_replica_request_socket.close()
            conn.sendall(json.dumps(True))
            conn.close()
        except Exception as e:
            conn.sendall(json.dumps(False))
            conn.close()
            print "Replica File Download Error, %s" % e

    def peer_server_host(self):
        """
        This method is used process client download request and file
        replication using pool of threads.
        """
        try:
            while True:
                while not self.peer_server_listener_queue.empty():
                    with futures.ThreadPoolExecutor(max_workers=8) as executor:
                        conn, addr = self.peer_server_listener_queue.get()
                        data_received = json.loads(conn.recv(1024))

                        if data_received['command'] == 'obtain_active':
                            fut = executor.submit(
                                self.peer_server_upload, conn, data_received)
                        elif data_received['command'] == 'request_replica':
                            fut = executor.submit(
                                self.peer_replica_download, conn, data_received)
        except Exception as e:
            print "Peer Server Hosting Error, %s" % e

    def data_resilience(self):
        """
        Data Resilience function is used to send command to the neighbouring
        peers asking them to make a request to this server to download the files
        to ensure duplicate copies are made.
        """
        clients = config["clients"]
        for file in self.peer.file_list:
            rep_index = self.peer.index
            for i in range(self.peer.replication_factor):
                if rep_index == len(clients) -1:
                    rep_index = 0
                else:
                    rep_index = rep_index + 1
                replica_request_socket = \
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                replica_request_socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                replica_request_socket.setsockopt(
                    socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                timeout = 0
                while timeout < 60:
                    try:
                        replica_request_socket.connect(
                            (clients[rep_index]["ip"], clients[rep_index]["port"]))
                        cmd_issue = {
                            'command' : 'request_replica',
                            'peer_id' : self.peer.peer_id,
                            'file_name' : file
                        }
                        replica_request_socket.sendall(json.dumps(cmd_issue))
                        rcv_data = replica_request_socket.recv(1024)
                        if rcv_data:
                            print "Replication of file: %s successfull!" % file
                            break
                    except Exception as e:
                        time.sleep(10)
                        timeout = timeout + 10
                replica_request_socket.close()

    def peer_server(self):
        """
        This method is used start peer server listener and peer server
        download deamon thread.
        """
        try:
            listener_thread = threading.Thread(target=self.peer_server_listener)
            listener_thread.setDaemon(True)

            operations_thread = threading.Thread(target=self.peer_server_host)
            operations_thread.setDaemon(True)

            dr_thread = threading.Thread(target=self.data_resilience)
            dr_thread.setDaemon(True)

            listener_thread.start()
            operations_thread.start()
            dr_thread.start()

            threads = []
            threads.append(listener_thread)
            threads.append(operations_thread)

            for t in threads:
                t.join()
        except Exception as e:
            print "Peer Server Error, %s" % e
            sys.exit(1)

    def peer_file_handler(self):
        """
        Peer file handler is deamon thread handling file update and
        file removal updater to Index Server.
        """
        try:
            while True:
                file_monitor_list = []
                for filename in os.listdir(SHARED_DIR):
                    file_monitor_list.append(filename)
                diff_list_add = list(
                    set(file_monitor_list) - set(self.peer.file_list))
                diff_list_rm = list(
                    set(self.peer.file_list) - set(file_monitor_list))
                if len(diff_list_add) > 0:
                    for file in diff_list_add:
                        self.peer.service.put(file, self.peer.peer_id)
                self.peer.file_list = file_monitor_list
                time.sleep(10)
        except Exception as e:
            print "File Handler Error, %s" % e
            sys.exit(1)

    def run(self):
        """
        Deamon thread for Peer Server and File Handler.
        """
        if self.name == "PeerServer":
            self.peer_server()
        elif self.name == "PeerFileHandler":
            self.peer_file_handler()

class Peer():
    def __init__(self, service, config, port, replica):
        """
        Constructor used to initialize class object.
        """
        self.peer_hostname = HOST_IP
        self.service = service
        self.config = config
        self.peer_port = port
        self.replication_factor = replica
        self.file_list = []
        self.peer_id = self.peer_hostname+":"+str(self.peer_port)
        for i in range(len(config["clients"])):
            if config["clients"][i]["ip"] == HOST_IP:
                index = i
                break
        self.index = index

    def get_file_list(self):
        """
        Obtain file list in shared dir.
        """
        try:
            for filename in os.listdir(SHARED_DIR):
                self.file_list.append(filename)
        except Exception as e:
            print "Error: retriving file list, %s" % e

    def register_peer(self):
        """
        Registering peer with Distributed Index Server.
        """
        try:
            self.get_file_list()
            print "Registering Peer with Server..."
            for file in self.file_list:
                response = self.service.put(file, self.peer_id)
                if response:
                    print "Peer Put Key: \'%s\' on server successful, " \
                          % (file)
                else:
                    print "Peer Put Key: \'%s\' on server unsuccessful, " \
                          % (file)
        except Exception as e:
            print "Registering Peer Error, %s" % e
            sys.exit(1)

    def search_file(self, file_name):
        """
        Search for a file in Index Server.

        @param file_name:      File name to be searched.
        """
        try:
            print "Searching file in the Server..."
            response = self.service.get(file_name)
            if not response:
                print "Peer Get value of Key: \'%s\' on server unsuccessful." \
                      % (file_name)
                return False
            print "Peer Get value of Key: \'%s\' on server successful, " \
                  % (file_name)
            self.file_peer_list = response
            return True
        except Exception as e:
            print "Search File Error..."
            return False

    def obtain(self, file_name, peer_request_id):
        """
        Download file from another peer.

        @param file_name:          File name to be downloaded.
        @param peer_request_id:    Peer ID to be downloaded.
        """
        try:
            peer_request_addr, peer_request_port = peer_request_id.split(':')
            peer_request_socket = \
                socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_request_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            peer_request_socket.setsockopt(
                socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            peer_request_socket.connect(
                (peer_request_addr, int(peer_request_port)))

            cmd_issue = {
                'command' : 'obtain_active',
                'file_name' : file_name
            }

            peer_request_socket.sendall(json.dumps(cmd_issue))

            f = open(SHARED_DIR+'/'+file_name, 'wb')
            while True:
                data = peer_request_socket.recv(10485760)
                if data:
                    f.write(data)
                else:
                    f.close()
                    break
            peer_request_socket.close()
            print "File downloaded successfully"
            return True
        except Exception as e:
            print "Obtain File Error..."
            print "Try different server!"
            return False


if __name__ == '__main__':
    """
    Main method starting deamon threads and peer operations.
    """
    try:
        args = get_args()
        with open(args.config) as f:
            config = json.loads(f.read())

        service = DIndexService(config)

        print "Starting Peer...",
        p = Peer(service, config, args.port, args.replica)
        print "Peer ID: %s" % (p.peer_id)
        p.service.establish_connection()
        p.register_peer()

        #print "Stating Peer Server Deamon Thread..."
        server_thread = PeerOperations(1, "PeerServer", p)
        server_thread.setDaemon(True)
        server_thread.start()

        #print "Starting File Handler Deamon Thread..."
        file_handler_thread = PeerOperations(2, "PeerFileHandler", p)
        file_handler_thread.setDaemon(True)
        file_handler_thread.start()

        while True:
            print "*" * 20
            print "Enter File Name to be Searched or \'q\' to exit"
            file_name = raw_input()
            if file_name == 'q':
                p.service.disable_connection()
                break
            result = p.search_file(file_name)
            if result:
                download = True
                while download:
                    if not p.file_peer_list:
                        print "All host servers are down..."
                        break
                    count = 0
                    for id in p.file_peer_list:
                        print "%s.Peer ID: %s" % (count,id)
                        count = count + 1
                    print "Enter index number of Peer ID to download the file from"
                    peer_request_id = int(raw_input())
                    status = p.obtain(file_name, p.file_peer_list[peer_request_id])
                    if status:
                        break
                    else:
                        p.file_peer_list.pop(peer_request_id)

    except Exception as e:
        print "main function error: %s" % e
        sys.exit(1)
    except (KeyboardInterrupt, SystemExit):
        print "Peer Shutting down..."
        p.service.disable_connection()
        time.sleep(1)
        sys.exit(1)

__author__ = 'arihant'
