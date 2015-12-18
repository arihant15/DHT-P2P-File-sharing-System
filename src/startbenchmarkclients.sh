gnome-terminal --window-with-profile=P2P -e "bash -c cd\ Peer1;python\ PeerBenchmark.py\ -c\ ../config.json\ -i\ 10000\ -e\ 20000\ -o\ 1;bash" &
#gnome-terminal --window-with-profile=P2P -e "bash -c cd\ Peer2;python\ PeerBenchmark.py\ -c\ ../config.json\ -i\ 10000\ -e\ 20000\ -o\ 2;bash" &
wait
