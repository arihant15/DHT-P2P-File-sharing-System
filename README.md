A Simple Distributed Peer-to-Peer File Sharing System:
	
	The system is written using Python programming language.

	Requirements:

	* Python version: 2.* , should be equal or greater than 2.6.

Below are the steps to be followed to execute and run the program.

1) Run Normal Program:
	
	Method 1:

	Open Project folder. Change directory to "src"

			$ cd src

	Folder "src" contains the script file "startservers.sh", "startclients.sh", the config file "config.json" and the src code for the system.

	config.json: contains the list of servers IP, Client IP and its corresponding port numbers in a JSON format. Verify and modify the IP and port as per the server connections.

	Distributed Indexing Server:

	1.1.1	File name “DIndexServer.py” contains the source code
		
	1.1.2	To execute the program, follow the below steps.

			$ python DIndexServer.py [-h] -c CONFIG -s SERVER

		Standard Arguments for talking to Distributed Index Server

		optional arguments:
		  -h, --help            show this help message and exit
		  -c CONFIG, --config CONFIG
		                        Config file of the network
		  -s SERVER, --server SERVER
		                        Server Port Number


		Note: * arugment -c and -s is mandatory

		Example:
			$ python DIndexServer.py -c config.json -s 3340
		
		The above example will start the distributed index server on socket port 3340.

	1.1.3	This outputs the below:

		src$ python DIndexServer.py -c config.json -s 3340
		Starting Distributed Indexing Server with Hash Index: 0 on Port: 3340
		Starting Distributed Indexing Server Listener... Done!


	Steps to Run Peer:

	1.2.1	Depending on the requirement, open n number of terminals (here n = 3).

	1.2.2	Change directory to Peer#(1/2/3)

	1.2.3	Execute the program:

			/src/Peer#$ Peer.py [-h] -c CONFIG -p PORT [-r REPLICA]

		Standard Arguments for talking to Distributed Index Server

		optional arguments:
		  -h, --help            show this help message and exit
		  -c CONFIG, --config CONFIG
		                        Config file of the network
		  -p PORT, --port PORT  Peer Server Port Number
		  -r REPLICA, --replica REPLICA
		                        Data Replication Factor

		Note: * arugment -c and -p is mandatory

		Example:
			/src/Peer#$ python Peer.py -c ../config.json -p 3350
		
		The above example will start the peer on socket port 3350.

	1.2.4	This outputs the below:  

		eg:
			/src/Peer#$ python Peer.py -c ../config.json -p 3350
			Starting Peer... Peer ID: 127.0.1.1:3352
			Registering Peer with Server...
			********************
			Enter File Name to be Searched or 'q' to exit
			text-1kb
			Searching file in the Server...
			Peer Get value of Key: 'text-1kb' on server successful, 
			0.Peer ID: 127.0.1.1:3350
			1.Peer ID: 127.0.1.1:3351
			Enter index number of Peer ID to download the file from
			0
			File downloaded successfully
			********************
			Enter File Name to be Searched or 'q' to exit

	Method 2:

		The process of starting the distributed index server and clients is automated using shell script.

		Requirements to run the shell script:

			1. gnome-terminal

		To execute the program, follow the below steps.

			src$ chmod +x startservers.sh
			src$ ./startservers.sh
			src$ chmod +x startclients.sh
			src$ ./startclients.sh

2) Run Benchmark Program:

	Method 1:

	Distributed Indexing Server:
	
	2.1.1	File name “DIndexServerBenchmark.py” contains the source code
		
	2.1.2	To run the program, follow the similar steps for running DIndexServer.py as stated above.

	Steps to Run Peer Benchmark:

	2.2.1	Follow the steps of Run Peer 1.2.1 and 1.2.2
	
	2.2.2	To execute the program, follow the below steps.

			$ PeerBenchmark.py [-h] -c CONFIG -i INDEX -e END -o OPERATION

		Standard Arguments for talking to Distributed Index Server

		optional arguments:
		  -h, --help            show this help message and exit
		  -c CONFIG, --config CONFIG
		                        Config file of the network
		  -i INDEX, --index INDEX
		                        key range start index
		  -e END, --end END     key range end index
		  -o OPERATION, --operation OPERATION
		                        operation: 1.Register & Search ops 2.Obtain ops

		Note: * arugment -c and -p is mandatory
		
		Example:
			/src/Peer#$ python PeerBenchmark.py -c ../config.json -i 10000 -e 20000 -o 1

	Method 2:

		The process of starting the distributed index server and clients benchmark is automated using shell script.

		Requirements to run the shell script:

			1. gnome-terminal

		To execute the program, follow the below steps.

			src$ chmod +x startbenchmarkservers.sh
			src$ ./startbenchmarkservers.sh
			src$ chmod +x startbenchmarkclients.sh
			src$ ./startbenchmarkclients.sh


AWS Scripts used to trigger the jobs using parallel-ssh:

neighbor.txt and active.txt contains the list of public ip address of the AWS EC2 instance.

start server:
	pssh -v -t 0 -l ubuntu -h neighbor.txt -x "-t -t -o StrictHostKeyChecking=no -i <pem file>" -P '~/AOS/PA3/startbenchmarkservers.sh'
start client:
	pssh -v -t 0 -l ubuntu -h active.txt -x "-t -t -o StrictHostKeyChecking=no -i <pem file>" -P '~/AOS/PA3/startbenchmarkclients.sh'
python status:	
pssh -v -t 0 -l ubuntu -h neighbor.txt -x "-t -t -o StrictHostKeyChecking=no -i <pem file>" -P 'ps -ef | grep python'
close python:	
pssh -v -t 0 -l ubuntu -h neighbor.txt -x "-t -t -o StrictHostKeyChecking=no -i <pem file>" 'pkill -9 python'