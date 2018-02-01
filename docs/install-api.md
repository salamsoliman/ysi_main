# Blockstack API 

Step-by-step instructions for deploying a Blockstack API node on Debian or 
Ubuntu are below.

- **Step 1:** Make sure you have Blockstack Core running locally (see [instructions](https://github.com/ysi/ysi-core/blob/master/README.md#quick-start)). 

- **Step 2:** Make sure you have [virtualenv installed](http://docs.python-guide.org/en/latest/dev/virtualenvs/). 
Then, setup the API:
``` 
$ sudo apt-get install -y python-pip memcached rng-tools python-dev libmemcached-dev zlib1g-dev libgmp-dev libffi-dev libssl-dev 
$ sudo service memcached start
$ sudo pip install virtualenv
$ sudo npm -g install aglio
$ virtualenv api && source api/bin/activate
$ git clone https://github.com/ysi/ysi-core.git
$ cd ysi-core/
$ pip install .
$ pip install -r api/requirements.txt
$ ysi setup_wallet
$ ysi api start
$ deactivate
$ ./build_docs.sh public_api
```

### Search Subsystem

If you want to enable the search subsystem in your installation, you can
follow the instructions [here](search.md).

### Nginx Deployment

For a production deployment we recommend using nginx and uwsgi:

- **Step 1:** Install nginx and uWSGI:
```
$ sudo apt-get install -y nginx
$ sudo pip install uwsgi
```
- **Step 2:** Copy [this sample nginx sites file](../api/nginx/config/nginx_sites-available/ysi_api) to

> /etc/nginx/sites-available/ysi_api

and edit the paths depending on the uwsgi ysi_api socket directory (defaults to /tmp/ysi_api.sock) 
You can test your nginx settings:
```
$ sudo nginx -t
```
- **Step 3:** Copy [this sample systemd service file](../api/nginx/config/systemd_system/ysi_api.service) to

> /etc/systemd/system/ysi_api.service

and edit the service user and ysi paths depending on where your ysi repo is located, and 
where your virtualenv is located. 

Note: The following sed commands will work if the virtualenv is currently active and your shell is in the repo's root directory.

```
$ sudo sed -i "s/User\=USER/User\=$USER/" /etc/systemd/system/ysi_api.service
$ sudo sed -i "s#/path/to/ysi#$PWD#" /etc/systemd/system/ysi_api.service
$ sudo sed -i "s#/path/to/virtualenv#$VIRTUAL_ENV#" /etc/systemd/system/ysi_api.service
```

- **Step 4:** Get a security certificate from [Let's Encrypt](https://letsencrypt.org/).
```
$ git clone https://github.com/certbot/certbot.git
$ cd certbot/
$ ./certbot-auto --nginx -d <your_domain>
```

And copy the cert files to the path given in the nginx sites file earlier.

- **Step 5:** Start nginx and the Blockstack API uwsgi server:
```
sudo systemctl restart ysi_api
sudo systemctl restart nginx
```

If you run into any issues, please [submit a Github issue](https://github.com/ysi/ysi-core/issues) and we'll update these
instructions.
