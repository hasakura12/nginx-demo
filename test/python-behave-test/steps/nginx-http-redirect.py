#!/usr/bin/env python3
import os
import unittest
import socket
import time
import pdb
import json
import requests
from sure import expect
import subprocess

HOST = os.getenv("HOST", "localhost")
HTTP_PORT = os.getenv("HTTP_PORT", 8888)
HTTPS_PORT = os.getenv("HTTPS_PORT", 443)
INSECURE = not os.getenv("INSECURE", True)
USERNAME = os.getenv("USERNAME", "user1")
PASSWORD = os.getenv("PASSWORD", "user1")

HTTP_TARGET_URL = 'http://%s:%s' % (HOST, HTTP_PORT)
HTTPS_TARGET_URL = 'https://%s:%s' % (HOST, HTTPS_PORT)


script_dir = os.path.dirname(__file__)

@then(u'I make GET request to http://localhost:8888 then I should get redirected and receive 200')
def step_impl(context):
    print("\nthen I make GET request to http://localhost:8888 then I should get redirected and receive 200...")

    full_url_path = '%s' % (HTTPS_TARGET_URL)
    print("to the following url... " + full_url_path)
    
    headers = {'Content-type': 'text/plain'}
    response = requests.get(full_url_path,
                            auth=(USERNAME, PASSWORD),
                            headers=headers,
                            verify=INSECURE)
    print("response.content was... " + str(response.content))

    response.status_code.should.equal(200)
    expect(str(response.content)).to.contain("Hello from Nginx server.")
