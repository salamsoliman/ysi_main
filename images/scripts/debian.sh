sudo apt-get update
sudo apt-get -y install python-dev git python-pip
git clone https://github.com/ysi/ysi.git
cd ysi
pip install -r requirements.txt
python setup.py build
sudo python setup.py install
