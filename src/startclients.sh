gnome-terminal --window-with-profile=P2P -e "bash -c cd\ Peer1;python\ Peer.py\ -c\ ../config.json\ -p\ 3350\ -r\ 1;bash" &
gnome-terminal --window-with-profile=P2P -e "bash -c cd\ Peer2;python\ Peer.py\ -c\ ../config.json\ -p\ 3351\ -r\ 1;bash" &
gnome-terminal --window-with-profile=P2P -e "bash -c cd\ Peer3;python\ Peer.py\ -c\ ../config.json\ -p\ 3352\ -r\ 1;bash" &
