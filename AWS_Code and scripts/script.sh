for dest in $(<neighbor.txt); do
  scp -i AOS.pem config.json ubuntu@${dest}:AOS/PA3
done
#for dest in $(<active.txt); do
#  scp -i AOS.pem PA1/PeerBenchmark-obtain/PeerBenchmark.py ubuntu@${dest}:AOS/PA1/PeerBenchmark-obtain
#done
#for dest in $(<neighbor.txt); do
#  scp -i AOS.pem PA1/PeerBenchmark-Reg/PeerBenchmark.py ubuntu@${dest}:AOS/PA1/PeerBenchmark-Reg
#done
#for dest in $(<neighbor.txt); do
#  scp -i AOS.pem PA1/PeerBenchmark-search/PeerBenchmark.py ubuntu@${dest}:AOS/PA1/PeerBenchmark-search
#done
#for dest in $(<neighbor.txt); do
#  scp -i AOS.pem PA1/CIndexServer.py ubuntu@${dest}:AOS/PA1
#done
#for dest in $(<neighbor.txt); do
#  scp -i AOS.pem Peer/PeerBenchmark1.py ubuntu@${dest}:AOS/PA3/Peer
#done
#for dest in $(<neighbor.txt); do
#  scp -i AOS.pem startbenchmarkclients2.sh ubuntu@${dest}:AOS/PA3
#done
#for dest in $(<neighbor.txt); do
#  scp -i AOS.pem filegen.py ubuntu@${dest}:AOS/PA3
#done
#sleep 10
#for dest in $(<neighbor.txt); do
#  ssh -i AOS.pem ubuntu@${dest} "~/AOS/PA3/startbenchmarkservers.sh" &
#done
#sleep 10
#for dest in $(<neighbor.txt); do
#  ssh -i AOS.pem ubuntu@${dest} "~/AOS/PA3/startbenchmarkclients.sh" &
#done
#sleep 30
#for dest in $(<neighbor.txt); do
#  ssh -i AOS.pem ubuntu@${dest} "pkill -9 python"
#done
