#!/bin/bash
############################################################################
#
# This script will create a folder `ysi` in your current directory
#   this folder will contain: 
#        a Python virtualenv with Blockstack-Core
#        a git clone of the Blockstack-Browser node app 
#                (with dependencies installed)
#        a `bin` directory with scripts:
#          ysi_browser_start.sh -> for starting core and browser
#          ysi_browser_stop.sh  -> for stopping browser
#          ysi_core_stop.sh    -> for stopping core
#          ysi_copy_api_pass.sh-> copies the API key to the clipboard
#
# The script will also install system dependencies using `apt`. For this, it
#  will attempt to `sudo` -- if you'd like to run this script without sudo,
#  you can pass the `--no-install` flag, but you will have to have installed
#  these dependencies prior to runnig the script.
#
# Finally, you must pass your desired wallet password to the script as an
#  argument. 
#
############################################################################

set -e

NO_INSTALL=0

if [ "$1" == "--no-install" ]
then
   NO_INSTALL=1
   BITCOIN_WALLET_PASSWORD="$2"
else
   BITCOIN_WALLET_PASSWORD="$1"
   if [ "$2" == "--no-install" ]
   then
       NO_INSTALL=1
   fi
fi

DIR=$PWD/ysi
CORE_VENV="$DIR/core-venv"

if [ -z "$BITCOIN_WALLET_PASSWORD" ]
then
    echo "You have to pass the desired wallet password to script as an argument."
    exit 1
fi

if [ -e "$DIR" ]
then
    echo "The directory '$DIR' already exists"
    exit 1
fi


############################################################################
# The sudoer section. If all of these are already installed on your system,
#  you can comment this out and run the script without it ever sudoing
############################################################################

if [ "$NO_INSTALL" -eq "0" ]
then
    sudo apt install -y curl xclip
    curl -sL https://deb.nodesource.com/setup_7.x | sudo -E bash -
    sudo apt update 
    sudo apt install -y python-pip python-dev libssl-dev libffi-dev rng-tools curl build-essential git nodejs
    sudo pip install virtualenv
fi

############################################################################

mkdir -p "$DIR"

virtualenv --python=python2.7 "$CORE_VENV"

"$CORE_VENV/bin/python" -m pip install git+https://github.com/ysi/virtualchain.git@rc-0.14.3
"$CORE_VENV/bin/python" -m pip install git+https://github.com/ysi/ysi-core.git@rc-0.14.3

"$CORE_VENV/bin/python" "$CORE_VENV/bin/ysi" setup -y --password "$BITCOIN_WALLET_PASSWORD"

cd "$DIR"

git clone https://github.com/ysi/ysi-browser.git -bv0.11.1
cd ysi-browser

npm install node-sass
npm install

echo "Installed Blockstack Core + Browser!"

# make some bin scripts.

mkdir "$DIR/bin"
cd "$DIR/bin"

START_PORTAL_NAME=ysi_browser_start.sh
STOP_PORTAL_NAME=ysi_browser_stop.sh
STOP_CORE_NAME=ysi_core_stop.sh
COPY_API_NAME=ysi_copy_api_pass.sh

echo "#!/bin/bash" > $START_PORTAL_NAME
echo "cd \"$DIR/ysi-browser\"" >> $START_PORTAL_NAME
echo "\"$CORE_VENV/bin/python\" \"$CORE_VENV/bin/ysi\" api status -y | grep 'true' > /dev/null" >> $START_PORTAL_NAME
echo "if [ \$? -ne 0 ]; then" >> $START_PORTAL_NAME
echo "\"$CORE_VENV/bin/python\" \"$CORE_VENV/bin/ysi\" api start -y --debug" >> $START_PORTAL_NAME
echo "fi" >> $START_PORTAL_NAME
echo "npm run dev-proxy 2>&1 > /tmp/rundev_proxy_out &" >> $START_PORTAL_NAME
echo "echo \"\$!\" > /tmp/devproxy.pid" >> $START_PORTAL_NAME
echo "echo > /tmp/rundev_out" >> $START_PORTAL_NAME
echo "npm run dev 2>&1 >> /tmp/rundev_out &" >> $START_PORTAL_NAME
echo "echo \"\$!\" > /tmp/dev.pid" >> $START_PORTAL_NAME
echo "tail -f /tmp/rundev_out | grep -m 1 \"Finished 'dev'\" > /dev/null" >> $START_PORTAL_NAME
echo "echo 'Running... connect at localhost:3000'" >> $START_PORTAL_NAME


echo "#!/bin/bash" > $STOP_PORTAL_NAME
echo "tokill=\$(cat /tmp/dev.pid)" >> $STOP_PORTAL_NAME
echo "echo 'Terminating process group of \$tokill'" >> $STOP_PORTAL_NAME
echo "kill -s SIGTERM -\$(ps -o pgid= \$tokill | cut -d\\  -f2)" >> $STOP_PORTAL_NAME
echo "echo 'Killed Blockstack Browser'" >> $STOP_PORTAL_NAME

echo "#!/bin/bash" > $STOP_CORE_NAME
echo "\"$CORE_VENV/bin/python\" \"$CORE_VENV/bin/ysi\" api stop -y" >> $STOP_CORE_NAME
echo "echo 'Stopped Blockstack Core'" >> $STOP_CORE_NAME

echo "#!/bin/bash" > $COPY_API_NAME
echo "grep api_password ~/.ysi/client.ini | sed 's/api_password = //g' | xclip -selection clipboard" >> $COPY_API_NAME

chmod +x $START_PORTAL_NAME
chmod +x $STOP_PORTAL_NAME
chmod +x $COPY_API_NAME
chmod +x $STOP_CORE_NAME

echo "Made app scripts!"
echo "You can add bins to your path with \$ export PATH=\$PWD/ysi/bin:\$PATH"
echo "You may need to add a protocol handler for your system, add a .desktop like the following and it should work: "
echo
echo "[Desktop Entry]"
echo "Type=Application"
echo "Terminal=false"
echo "Exec=bash -c 'xdg-open http://localhost:3000/auth?authRequest=\$(echo \"%u\" | sed s,ysi:/*,,)'"
echo "Name=Blockstack-Browser"
echo "MimeType=x-scheme-handler/ysi;"
echo
echo
