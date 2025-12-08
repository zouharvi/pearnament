# sets up a local VM that runs pearmut and tunnels it through ngrok

sudo snap install multipass
multipass launch --name pearmut-box
multipass mount ~/pearmut/data_vm/ pearmut-box:/home/ubuntu/data_vm
multipass shell pearmut-box

sudo apt update
sudo apt install python3-pip -y
python3 -m pip config set global.break-system-packages true
pip install pearmut
export PATH=$PATH:/home/ubuntu/.local/bin
sudo snap install ngrok
ngrok authtoken YOUR_NGROK_AUTH_TOKEN_HERE

ngrok http --url=pearmut.ngrok.io 8001
nohup pearmut run --port 8001 --server https://pearmut.ngrok.io 1> pearmut.log 2>pearmut.err &