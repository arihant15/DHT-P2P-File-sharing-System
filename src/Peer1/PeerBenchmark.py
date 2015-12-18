#!/usr/bin/python

import socket
import time
import json
import os
import threading
import argparse
from DIndexServiceBenchmark import DIndexService
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
    parser.add_argument('-i', '--index',
                        type=int,
                        required=True,
                        action='store',
                        help='key range start index')
    parser.add_argument('-e', '--end',
                        type=int,
                        required=True,
                        action='store',
                        help='key range end index')
    parser.add_argument('-o', '--operation',
                        type=int,
                        required=True,
                        action='store',
                        help='operation: 1.Register & Search ops 2.Obtain ops')
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
            '''
            while True:
                data = f.readline()
                if data:
                    conn.sendall(data)
                else:
                    break
            '''
            f.close()
            conn.sendall('')
            conn.close()
        except Exception as e:
            print "File Upload Error, %s" % e

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
        except Exception as e:
            print "Peer Server Hosting Error, %s" % e

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

            listener_thread.start()
            operations_thread.start()

            threads = []
            threads.append(listener_thread)
            threads.append(operations_thread)

            for t in threads:
                t.join()
        except Exception as e:
            print "Peer Server Error, %s" % e
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
    def __init__(self, service, index, end):
        """
        Constructor used to initialize class object.
        """
        self.peer_hostname = HOST_IP
        self.service = service
        self.file_list = []
        self.peer_port = self.get_free_socket()
        self.peer_id = self.peer_hostname+":"+str(self.peer_port)
        self.key_start = index
        self.key_end = end

    def get_file_list(self):
        """
        Obtain file list in shared dir.
        """
        try:
            for filename in os.listdir(SHARED_DIR):
                self.file_list.append(filename)
        except Exception as e:
            print "Error: retriving file list, %s" % e

    def get_free_socket(self):
        """
        This method is used to obtain free socket port for the registering peer
        where the peer can use this port for hosting file as a server.

        @return free_socket:    Socket port to be used as a Peer Server.
        """
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            peer_socket.bind(('', 0))
            free_socket = peer_socket.getsockname()[1]
            peer_socket.close()
            return free_socket
        except Exception as e:
            print "Obtaining free sockets failed: %s" % e
            sys.exit(1)

    def register_peer(self):
        """
        Registering peer with Distributed Index Server.
        """
        try:
            self.get_file_list()
            num_files = len(self.file_list)
            total_ops = self.key_end - self.key_start
            run_ops = total_ops/num_files
            print "Staring Benchmark Register Peer with Server..."
            t1 = time.time()
            for i in range(run_ops):
                for file in self.file_list:
                    self.service.put(file, self.peer_id)
            t2 = time.time()
            total = run_ops * num_files
            print "%s Register operations = %s sec" % (total,t2-t1)
            print "per Register operation = %s sec" % ((t2-t1)/total)
            print "per Register operation = %s msec" % (((t2-t1)/total)*1000)
        except Exception as e:
            print "Registering Peer Error, %s" % e
            sys.exit(1)

    def search_file(self, file_name):
        """
        Search for a file in Index Server.

        @param file_name:      File name to be searched.
        """
        try:
            total_ops = self.key_end - self.key_start
            run_ops = total_ops/10
            print "Staring Benchmark Searching file in the Server..."
            t1 = time.time()
            for i in range(run_ops):
                for j in range(1,11,1):
                    file_name = "text-"+str(j)+"kb"
                    self.service.get(file_name)
            t2 = time.time()
            print "%s Search operations = %s sec" % (total_ops,t2-t1)
            print "per Search operation = %s sec" % ((t2-t1)/total_ops)
            print "per Search operation = %s msec" % (((t2-t1)/total_ops)*1000)
        except Exception as e:
            print "Search File Error, %s" % e

    def obtain(self, file_name, peer_request_id):
        """
        Download file from another peer.

        @param file_name:          File name to be downloaded.
        @param peer_request_id:    Peer ID to be downloaded.
        """
        try:
            total_ops = self.key_end - self.key_start
            run_ops = total_ops/10
            print "Staring Benchmark Obtain file from Peer..."
            t1 = time.time()
            for i in range(run_ops):
                for j in range(1,11,1):
                    peer_request_addr, peer_request_port = peer_request_id.split(':')
                    peer_request_socket = \
                        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_request_socket.setsockopt(
                        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    peer_request_socket.setsockopt(
                        socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    peer_request_socket.connect(
                        (peer_request_addr, int(peer_request_port)))
                    file_name = "text-"+str(j)+"kb"
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
            t2 = time.time()
            print "%s Obtain operations = %s sec" % (total_ops,t2-t1)
            print "per Obtain operation = %s sec" % ((t2-t1)/total_ops)
            print "per Obtain operation = %s msec" % (((t2-t1)/total_ops)*1000)
        except Exception as e:
            print "Obtain File Error, %s" % e
            print "Try different server!"

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
        p = Peer(service, args.index, args.end)
        print "Peer ID: %s" % (p.peer_id)

        server_thread = PeerOperations(1, "PeerServer", p)
        server_thread.setDaemon(True)
        server_thread.start()

        if args.operation == 1:
            p.service.establish_connection()
            time.sleep(5)
            p.register_peer()
            p.service.disable_connection()
            print "Flushing..."
            time.sleep(10)
            p.service.establish_connection()
            p.search_file("dummy")
            p.service.disable_connection()
        elif args.operation == 2:
            time.sleep(5)
            p.obtain("dummy", "127.0.1.1:3350")

    except Exception as e:
        print "main function error: %s" % e
        sys.exit(1)
    except (KeyboardInterrupt, SystemExit):
        print "Peer Shutting down..."
        service.disable_connection()
        time.sleep(1)
        sys.exit(1)

__author__ = 'arihant'
