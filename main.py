# -*- coding: utf-8 -*-

#import google.auth
#import google.oauth2.credentials
import os
import requests

### AUTH
# credentials_key = "./key.json"

# Set credentials
#credentials = google.oauth2.credentials.Credentials(
#    'access_token',
#    refresh_token = 'refresh_token',
#    token_uri = 'token_uri',
#    client_id = 'client_id',
#    client_secret = 'client_secret'
#)

url = 'https://virtualracingschool.appspot.com/#/Home'

# Get cookie from file
with open("./vrs-cookie", "r") as cookie:
    for line in cookie:
        if "jsessionid" in line.lower():
            cookie_vrs = dict(JSESSIONID=line.split("=")[1])

print(cookie_vrs)


r = requests.get(url, cookies=cookie_vrs)
print(r.text)

for line in r.text:
    if "pack" in line.lower():
        print(line)