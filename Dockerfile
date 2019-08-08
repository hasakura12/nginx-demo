FROM nginx
CMD ["mkdir", "-p", "/etc/ssl/private/nginx_demo.com"]
CMD ["mkdir", "-p", "/etc/ssl/certs/nginx_demo.com"]
CMD ["mkdir", "-p", "/var/www/nginx_demo.com"]
CMD ["mkdir", "-p", "/etc/nginx/nginx_demo.com"]

COPY self.crt /etc/ssl/certs/nginx_demo.com/self.crt
COPY self.key /etc/ssl/private/nginx_demo.com/self.key
COPY nginx.conf /etc/nginx/nginx.conf
COPY .htpasswd /etc/nginx/nginx_demo.com/.htpasswd
COPY index.html /var/www/nginx_demo.com/index.html

CMD exec nginx -g 'daemon off;'