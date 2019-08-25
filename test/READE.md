## TL;DR
We use Python BDD test framework `bahave` to test a Nginx image.

Simply execute the script:
```
$ ./automated_test.sh
```


### Test locally
When running locally, you **need** to start Nginx container manually first
```
# start nginx-demo docker image first
$ cd ../
$ docker-compose up -d

$ cd test
$ sudo pip install behave sure
$ behave test/python-behave-test/*.feature

Feature: Rediect HTTP to HTTPs # python-behave-test/nginx-http-redirect.feature:1

  Scenario: Consume http://localhost:8888                                                         # python-behave-test/nginx-http-redirect.feature:2
    When a Nginx container is running                                                             # python-behave-test/steps/nginx-monitoring.py:22 0.000s
    Then I make GET request to http://localhost:8888 then I should get redirected and receive 200 # python-behave-test/steps/nginx-http-redirect.py:25 0.059s

Feature: Expose Nginx monitoring endpoint at localhost:8081 # python-behave-test/nginx-monitoring.feature:1

  Scenario: Consume monitoring endpoint at localhost:8081                                                # python-behave-test/nginx-monitoring.feature:2
    When a Nginx container is running                                                                    # python-behave-test/steps/nginx-monitoring.py:22 0.000s
    Then I make GET request to localhost:8081 and I receive 200 response with details from /nginx_status # python-behave-test/steps/nginx-monitoring.py:33 0.007s

2 features passed, 0 failed, 0 skipped
2 scenarios passed, 0 failed, 0 skipped
4 steps passed, 0 failed, 0 skipped, 0 undefined
Took 0m0.066s
```

### Test using Docker Image
When running using docker images, `docker-compose.yaml` will take care of starting both `nginx-demo` and `nginx-python-behave-test` images. So you need to make sure that Nginx container is **NOT** running prior to this otherwise port will be occupied.
```
# change dir to /nginx/test

$ docker build -t hasakura12/nginx-python-behave-test .
$ docker tag hasakura12/nginx-python-behave-test hasakura12/nginx-python-behave-test:1.00
$ docker login
$ docker push hasakura12/nginx-python-behave-test:1.00
$ docker-compose up -d
Starting nginx-python-behave-test ... done
Starting nginx         ... done
```

What `docker-compose up -d` does is to spin up two docker containers, nginx and nginx-python-behave-test as you could see in [docker-compose.yaml](docker-compose.yaml):
```
version: '3'
services:
  behave:
    image: hasakura12/nginx-python-behave-test:1.00
    container_name: nginx-python-behave-test
    volumes:
      - "./python-behave-test:/usr/src/python-behave-test:ro"
    env_file:
      - ./test.env
  nginx:
      image: hasakura12/nginx-demo:1.00
      container_name: nginx
      ports:
          - 443:443
          - 8888:8888
          - 8081:8081
      restart: always
```
`nginx-python-behave-test` container will run tests by making http request. After that it exits, so you will not see it running if you do `docker ps`
```
CONTAINER ID        IMAGE                        COMMAND                  CREATED              STATUS              PORTS                                                                          NAMES
d5f784285a8d        hasakura12/nginx-demo:1.00   "/bin/sh -c 'exec ng…"   About a minute ago   Up 1 second         0.0.0.0:443->443/tcp, 0.0.0.0:8081->8081/tcp, 80/tcp, 0.0.0.0:8888->8888/tcp   nginx
Hisashis-MacBook-Pro:test hisashi.asakura$ docker ps -a
```

Check `nginx-python-behave-test`'s log output
```
$ docker logs nginx-python-behave-test
 Scenario: Consume monitoring endpoint at localhost:8081                                                # nginx-monitoring.feature:2
    When a Nginx container is running                                                                    # steps/nginx-monitoring.py:22
    Then I make GET request to localhost:8081 and I receive 200 response with details from /nginx_status # steps/nginx-monitoring.py:33

Feature: Rediect HTTP to HTTPs # nginx-http-redirect.feature:1

  Scenario: Consume http://localhost:8888                                                         # nginx-http-redirect.feature:2
    When a Nginx container is running                                                             # steps/nginx-monitoring.py:22
    Then I make GET request to http://localhost:8888 then I should get redirected and receive 200 # steps/nginx-http-redirect.py:25

2 features passed, 0 failed, 0 skipped
2 scenarios passed, 0 failed, 0 skipped
4 steps passed, 0 failed, 0 skipped, 0 undefined
Took 0m0.023s
```

You can see the tests were successfully run and they both passed.
```
2 features passed, 0 failed, 0 skipped
2 scenarios passed, 0 failed, 0 skipped
4 steps passed, 0 failed, 0 skipped, 0 undefined
```