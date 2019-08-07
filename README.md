# Get Nginx Server Up and Running in Linux Ubuntu
## Index
- [Useful Nginx Commands](#useful_commands)
- [Install and Run Nginx from package manager](#install_package_manager)
- [Install and Run Nginx from source](#install_from_source)
- [Reverse Proxy Demo](#reverse_proxy)
  - [Add header to proxy request](#reverse_proxy_header)
- [Load Balancing Demo](#load_balancing)
  - [Enable Sticky Session](#load_balancing_sticky_session)
  - [Enable Load Balancing based on # of ](#load_balancing_policy)connections
- [Virtual Host's Resource Demo](#virtual_host)
  - [Add redirect](#virtual_host_redirect)
  - [Add rewrite](#virtual_host_rewrite)
  - [Disable access log example](#virtual_host_disable_access_log)
  - [Enable GZIP for faster response](#virtual_host_gzip)
  - [Enable caching](#virtual_host_enable_cache)
  - [Enable HTTPS](#virtual_host_enable_https)
  - [Redirect HTTP to HTTPS](#virtual_host_redirect_https)
  - [Enable Basic Auth (with password) for ](#virtual_host_enable_basic_auth)endpoint resources
  - [Disable XSS (cross site script sharing)](#virtual_host_disable_xss)


## Useful Nginx Commands <a name="useful_commands"></a>
```
# send reload singal for a new config to take an effect
nginx -s reload

# -t to test syntax of the config, which is specified by -c
nginx -t -c /etc/nginx/nginx.conf
```

## Install and Run Nginx from package manager <a name="install_package_manager"></a>
1. `apt update`
2. `apt install nginx`
3. `systemctl status nginx` should return `running` status
4. `curl localhost` should return a html page

Alternatively, you can build and run Nginx from the source (more convenient for adding/removing modules)
## Install and Run Nginx from the source <a name="install_from_source"></a>
1. `wget https://nginx.org/download/nginx-1.17.2.tar.gz`
2. `tar -xvzf nginx-1.17.2.tar.gz`
3. `cd nginx-1.17.2`
4. `./configure` should return an error like 
```
./configure: error: the HTTP rewrite module requires the PCRE library
```
5. `apt install build-essential`
6. `apt install libpcre3 libpcre3-dev zlib1g zlib1g-dev libssl-dev`
7. `./configure` again with parameters:
```
./configure \
  --sbin-path=/usr/sbin/nginx \
  --conf-path=/etc/nginx/nginx.conf \
  --error-log-path=/var/log/nginx/error.log \
  --http-log-path=/var/log/nginx/access.log \
  --with-pcre --pid-path=/var/run/nginx.pid
```
And should return below this time:
```
Configuration summary
  + using system PCRE library
  + OpenSSL library is not used
  + using system zlib library

  nginx path prefix: "/usr/local/nginx"
  nginx binary file: "/usr/local/nginx/sbin/nginx"
  nginx modules path: "/usr/local/nginx/modules"
  nginx configuration prefix: "/usr/local/nginx/conf"
  nginx configuration file: "/usr/local/nginx/conf/nginx.conf"
  nginx pid file: "/usr/local/nginx/logs/nginx.pid"
  nginx error log file: "/usr/local/nginx/logs/error.log"
  nginx http access log file: "/usr/local/nginx/logs/access.log"
  nginx http client request body temporary files: "client_body_temp"
  nginx http proxy temporary files: "proxy_temp"
  nginx http fastcgi temporary files: "fastcgi_temp"
  nginx http uwsgi temporary files: "uwsgi_temp"
  nginx http scgi temporary files: "scgi_temp"
```
8. Compile it `make`
9. Check Nginx version `nginx -V`
10. `Systemctl restart nginx`
11. `curl http://localhost` should return a html page


## Reverse Proxy Demo <a name="reverse_proxy"></a>
![alt text](imgs/reverse_proxy.png "Reverse Proxy")
Will create two servers from Nginx and PHP.

1. Up PHP server
```
cat > index.php << EOF
<?php
echo "hello from php server\n";
echo "Path: " . $_SERVER['REQUEST_URI'];
EOF

php -S localhost:9999 index.php
curl localhost:9999
```

2. Up Nginx server
```
cat > nginx.conf << EOF
events {}
http {
 
  server {
    listen 8888;
 
    location / {
        return 200 "Hello from custom nginx.conf\n";
    }
 
    location /php {
        # reverse proxy: should end with trailing /
        proxy_pass http://localhost:9999/;
    }
  }
}
EOF


nginx -c $PWD/nginx.conf
curl localhost:8888
```

3. Hit PHP server through Nginx (i.e. testing Nginx Reverse proxy)
```
curl localhost:9999/php
```
which should return
```
hello from php server
Path: /
```

### Add header to proxy request <a name="reverse_proxy_header"></a>
1. Modify the Nginx config and add a line
`proxy_set_header Host $host;`

`vim nginx.conf` and paste in the below:
```
events {}
http {

  server {
    listen 8888;

    location / {
        return 200 "Hello from custom nginx.conf\n";
    }

    location /php {
        # reverse proxy: should end with trailing /
        proxy_pass http://localhost:9999/;
        # set header for proxy request because add_header won't propagate to proxy header
        proxy_set_header Host $host;
    }
  }
}
```

Then reload the config:
```
nginx -s reload

# hit the Nginx server
curl localhost:8888
```

2. Modify index.php to return a header info

`vim index.php` and paste in the below:
```
<?php
echo "hello from php server\n";
echo "Path: " . $_SERVER['REQUEST_URI'];
echo "\n";
# return header info
var_dump(getallheaders());
```

```
# Then start a PHP server again:
php -S localhost:9999 index.php

# hit the PHP server
curl localhost:8888/php
```
should return a host header
```
hello from php server
Path: /
array(4) {
  ["Host"]=>
  string(9) "localhost"
  ["Connection"]=>
  string(5) "close"
  ["User-Agent"]=>
  string(11) "curl/7.47.0"
  ["Accept"]=>
  string(3) "*/*"
}
```


## Load Balancing Demo <a name="load_balancing"></a>
![alt text](imgs/load_balancer.png "Load Balancer")
1. Up two PHP servers

From a shell:
```
# redirect STDIN to index1.php
cat > index1.php << EOF
<?php
echo "hello from php server 1\n";
echo "Path: " . $_SERVER['REQUEST_URI'];
echo "\n";
# return header info
var_dump(getallheaders());
EOF

# Up PHP server 1
php -S localhost:10001 index1.php
```

From another shell:
```
# redirect STDIN to index2.php
cat > index2.php << EOF
<?php
echo "hello from php server 2\n";
echo "Path: " . $_SERVER['REQUEST_URI'];
echo "\n";
# return header info
var_dump(getallheaders());
EOF

# Up PHP server 2
php -S localhost:10002 index2.php
```

Test two PHP servers are running:

`curl localhost:10001`
should return:
```
hello from php server 1
Path: /
array(3) {
  ["Host"]=>
  string(15) "localhost:10001"
  ["User-Agent"]=>
  string(11) "curl/7.47.0"
  ["Accept"]=>
  string(3) "*/*"
}
```
Likely, `curl localhost:10002` should return:
```
hello from php server 2
Path: /
array(3) {
  ["Host"]=>
  string(15) "localhost:10002"
  ["User-Agent"]=>
  string(11) "curl/7.47.0"
  ["Accept"]=>
  string(3) "*/*"
}
```

2. Add load balancing config to `nginx.conf`
```
events {}
http {
  # load balancing (must be under http{} context)
  upstream php_servers {
    server localhost:10001;
    server localhost:10002;
  }

  server {
     listen 8888;

    # reverse proxy
    location / {
        # reverse proxy: should end with trailing /
        # specify upstream name to enable load balancing
        proxy_pass http://php_servers;

        # set header for proxy request because add_header won't propagate to proxy header
        proxy_set_header Host $host;
    }

  }
}
```

Reload the config:
`nginx -s reload`

Hit the load balancer: 
` while sleep 0.5; do curl localhost:8888; done`
should return responses from the two PHP servers
```
hello from php server 1
Path: /
array(4) {
  ["Host"]=>
  string(9) "localhost"
  ["Connection"]=>
  string(5) "close"
  ["User-Agent"]=>
  string(11) "curl/7.47.0"
  ["Accept"]=>
  string(3) "*/*"
}
hello from php server 2
Path: /
array(4) {
  ["Host"]=>
  string(9) "localhost"
  ["Connection"]=>
  string(5) "close"
  ["User-Agent"]=>
  string(11) "curl/7.47.0"
  ["Accept"]=>
  string(3) "*/*"
}
hello from php server 1
Path: /
array(4) {
  ["Host"]=>
  string(9) "localhost"
  ["Connection"]=>
  string(5) "close"
  ["User-Agent"]=>
  string(11) "curl/7.47.0"
  ["Accept"]=>
  string(3) "*/*"
}
```

### Enable Sticky Session <a name="load_balancing_sticky_session"></a>
Simply add `ip_hash;` line inside the upstream php_servers{} context.
```
# load balancing (must be under http{} context)
  upstream php_servers {
    # enable sticky session by creating hash table for IPs and proxy requests
    ip_hash;

    server localhost:10001;
    server localhost:10002;
  }
```
Then reload the config `nginx -s reload`

### Enable Load Balancing based on # of connections <a name="load_balancing_policy"></a>
Simply add `least_conn;` line inside the upstream php_servers{} context.
```
# load balancing (must be under http{} context)
  upstream php_servers {
    # enable sticky session by creating hash table for IPs and proxy requests
    #ip_hash;

    # load balance based on # of connections
    least_conn;

    server localhost:10001;
    server localhost:10002;
  }
```
Then reload the config `nginx -s reload`

## Virtual Host's Resource Demo (location{} context) <a name="virtual_host"></a>
Add endpoint resources to the virtual host `server{}` context:
```
# virtual host config
  server {
    # by default Nginx listens to port 80
    listen 8888;

    # set domain/IP
    server_name nginx_demo.com;

    # set the root path from which a static request is being served
    root /var/www/site;


    # exact match for resource
    location = /exact {
        return 200 "hello from $uri \n";
    }

    # regex match
    location ~ /regex[mM]atch {
        return 200 "hello from $uri \n";
    }

    # case-insensitive
    location ~* /caseInsensitive[1-3] {
        return 200 "hello from $uri \n";
    }

    # prefix match - pretty much a fallback 
    location / {
        try_files $uri $uri/ index.html;
        return 200 "hello from nginx_demo.com \n";
    }


    # reverse proxy
    location /proxy {
        # reverse proxy: should end with trailing /
        # specify upstream name to enable load balancing
        proxy_pass http://php_servers;

        # set header for proxy request because add_header won't propagate to proxy header
        proxy_set_header Host $host;
    }
  }
}
```
Test syntax and reload the config:
```
nginx -t -c /etc/nginx/demo/nginx.conf
nginx -s reload
```

Test endpoints:
```
curl localhost:8888/exact
hello from /exact

curl localhost:8888/regexmatch
hello from /regexmatch

curl localhost:8888/regexMatch
hello from /regexMatch

curl localhost:8888/caseinsensitive1
hello from /caseinsensitive1

curl localhost:8888/caseInsensitive1
hello from /caseInsensitive1

curl localhost:8888/fallback
hello from nginx_demo.com
```

### Add redirect <a name="virtual_host_redirect"></a>
![alt text](imgs/request.png "Request")
![alt text](imgs/redirect_response.png "Redirect response")
Simply return `return 307 /redirectedPath` inside a location{} context.
```
http {
  ...
  server {
    # redirect a request to /redirect to /exact
    location /redirect {
        return 307 /exact;
    }
  }
}
```
Test syntax and reload the config:
```
nginx -t -c /etc/nginx/demo/nginx.conf
nginx -s reload
```

Hit /redirect and should get 307:
```
curl localhost:8888/redirect
<html>
<head><title>307 Temporary Redirect</title></head>
<body bgcolor="white">
<center><h1>307 Temporary Redirect</h1></center>
<hr><center>nginx/1.10.3 (Ubuntu)</center>
</body>
</html>

# follow redirection by passing -L option
curl localhost:8888/redirect -L
hello from /exact
```

### Add rewrite <a name="virtual_host_rewrite"></a>
![alt text](imgs/request.png "Request")
![alt text](imgs/rewrite_response.png "Rewrite response")
```
http {
  ...
  server {
    # rewrite a request to /rewritten
    rewrite ^/rewrite /rewritten;
    location /rewritten {
        return 200 "hello from $uri \n";
    }
  }
}
```
```
nginx -t -c /etc/nginx/demo/nginx.conf
nginx -s reload
curl localhost:8888/rewrite
````
should return `hello from /rewritten`

### Disable access log example <a name="virtual_host_disable_access_log"></a>
```
# disable access log for .css/js/jpg/png extentions
location ~* \.(css|js|jpg|png)$ {
    access_log off;
    return 200 "hello from $uri, access log is disabled. \n";
}
```

### Enable GZIP for faster response <a name="virtual_host_gzip"></a>
```
http {
  # enable GZIP for performance
  gzip on;
  gzip_comp_level 3;
  gzip_types text/css;
  gzip_types text/javascript;

  server {
    ...
    location ~* \.(css|js|jpg|png)$ {
        # return header attributes
        add_header Cache-Control public;
        add_header Pragma public;
        add_header Vary Accept-Encoding;
        add_header metadata "this is metadata";
        expires 30d;

        # disable access log for .css/js/jpg/png extentions
        access_log off;

        try_files $uri $uri/ =400;
    }
  }
}
```
and `curl -I -H "Accept-Encoding: gzip" localhost:8888/test.css`
should return:
```
HTTP/1.1 200 OK
Server: nginx/1.10.3 (Ubuntu)
Date: Wed, 07 Aug 2019 14:39:08 GMT
Content-Type: text/css
Connection: keep-alive
Expires: Fri, 06 Sep 2019 14:39:08 GMT
Cache-Control: max-age=2592000
Cache-Control: public
Pragma: public
Vary: Accept-Encoding
metadata: this is metadata
Content-Encoding: gzip
```
Look at the last line:
`Content-Encoding: gzip`.

### Enable caching <a name="virtual_host_enable_cache"></a>
```
# disable access log for .css/js/jpg/png extentions
location ~* \.(css|js|jpg|png)$ {
    # return header attributes
    add_header Cache-Control public;
    add_header Pragma public;
    add_header Vary Accept-Encoding;
    add_header metadata "this is metadata";
    expires 30d;

    access_log off;
    return 200 "hello from $uri, access log is disabled. \n";
}
```

### Enable HTTPS <a name="virtual_host_enable_https"></a>
First create a self signed certificate and a private key:
```
mkdir /etc/nginx/demo/ssl

# create a private key and self-signed cert
openssl req \
    -x509 \
    -days 90 \
    -nodes \
    -newkey rsa:2048 \
    -keyout /etc/nginx/demo/ssl/self.key \
    -out /etc/nginx/demo/ssl/self.crt
```

Then configure HTTPs Virtual host to use the created cert and key:
```
server {
    # by default Nginx listens to port 80
    listen 443 ssl;

    # enable HTTPS
    ssl_certificate /etc/nginx/demo/ssl/self.crt;
    ssl_certificate_key /etc/nginx/demo/ssl/self.key;
}
```
`curl https://localhost:443/ -k` should return:
```
hello from nginx_demo.com
```

### Redirect HTTP to HTTPS <a name="virtual_host_redirect_https"></a>
Create a virtual host for HTTP that listens to 8888, and redirects all requests to https:
```
# virtual host config for HTTP
server {
  listen 8888;

  # redirect HTTP to HTTPS
  return 301 https://$host/$request_uri;
}
```

`curl localhost:8888/ -L -k -I`
should return:
```
HTTP/1.1 301 Moved Permanently
Server: nginx/1.10.3 (Ubuntu)
Date: Wed, 07 Aug 2019 15:08:02 GMT
Content-Type: text/html
Content-Length: 194
Connection: keep-alive
Location: https://localhost//

HTTP/1.1 200 OK
Server: nginx/1.10.3 (Ubuntu)
Date: Wed, 07 Aug 2019 15:08:02 GMT
Content-Type: text/plain
Content-Length: 27
Connection: keep-alive
```
The first response 301 and the line `Location: https://localhost//` confirms it's redirected to HTTPS.


### Enable Basic Auth (with password) for endpoint resources <a name="virtual_host_enable_basic_auth"></a>
```
# install a package
apt install apache2-utils -y

# create a password using htpasswd command
htpasswd -c /etc/nginx/demo/.htpasswd user1
```
Modify `nginx.conf`
```
# virtual host config for HTTPs
server {
  # by default Nginx listens to port 80
  listen 443 ssl;

  # enable HTTPS
  ssl_certificate /etc/nginx/demo/ssl/self.crt;
  ssl_certificate_key /etc/nginx/demo/ssl/self.key;

  # enable basic auth with password
  auth_basic "Password protected";
  auth_basic_user_file /etc/nginx/demo/.htpasswd;
}

```
`curl https://localhost:443 -k -u user1:user1` should return:
```
hello from nginx_demo.com
```

### Disable XSS (cross site script sharing) <a name="virtual_host_disable_xss"></a>
```
server {
  # disable cross site script sharing
	add_header X-Frame-Options "SAMEORIGIN";
	add_header X-XSS-Protection "1; mode-block";
}
```

`curl https://localhost:443 -k -u user1:user1 -I` should return:
```
HTTP/1.1 200 OK
Server: nginx/1.10.3 (Ubuntu)
Date: Wed, 07 Aug 2019 15:28:04 GMT
Content-Type: text/html
Content-Length: 26
Last-Modified: Wed, 07 Aug 2019 12:28:22 GMT
Connection: keep-alive
ETag: "5d4ac3e6-1a"
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode-block
Accept-Ranges: bytes
```
The lines 
```
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode-block
``` 
confirms XSS disabled.


## Ref
- [Nginx config pitfalls and best practices](https://www.nginx.com/resources/wiki/start/topics/tutorials/config_pitfalls/)