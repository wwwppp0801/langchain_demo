import os
import requests
import yaml
import json
import sys
import time
import re
import urllib3


### can be found in https://github.com/transitive-bullshit/chatgpt-well-known-plugin-finder

_openapis=[
#"https://www.expedia.com",
#"https://fiscalnote.com",
#"https://www.instacart.com",
#"https://www.kayak.com",
#"https://www.opentable.com",
#"https://www.shopify.com",
"https://slack.com",
"https://www.klarna.com",
"https://zapier.com",
#"https://pricerunner.se",
"https://www.wolframalpha.com",
"https://www.wolframcloud.com",
"https://api.speak.com",
#"https://x6lq6i-5001.csb.app",
"https://datasette.io",
"https://www.joinmilo.com",
        ]
if not os.path.exists("openapi"):
    os.makedirs("openapi")
## get all openapi files
for _openapi in _openapis:
    try:
        requests.packages.urllib3.disable_warnings()
        # request path "/.well-known/ai-plugin.json"
        _ai_plugin = _openapi + "/.well-known/ai-plugin.json"
        _ai_plugin_file = requests.get(_ai_plugin,verify=False ,proxies={"http": os.environ.get("HTTP_PROXY", ""), "https": os.environ.get("HTTP_PROXY", "")})
        # if http status code is not 200, skip
        if _ai_plugin_file.status_code != 200:
            print("Error: " + _ai_plugin
                  + " status code: " + str(_ai_plugin_file.status_code)
                  + " skip")
            continue
        else:
            print("Success: " + _ai_plugin)
        _openapi_manifest_file_name = _openapi.split("/")[2] + ".json"
        with open("openapi/" + _openapi_manifest_file_name, "w") as f:
            f.write(_ai_plugin_file.text)
        # get openapi file path from "ai-plugin.json"
        _openapi_yaml = json.loads(_ai_plugin_file.text)["api"]["url"]

        

        _openapi_file = requests.get(_openapi_yaml,verify=False,proxies={"http": os.environ.get("HTTP_PROXY", ""), "https": os.environ.get("HTTP_PROXY", "")})
        # if http status code is not 200, skip
        if _openapi_file.status_code != 200:
            print("Error: " + _openapi
                  + " status code: " + str(_openapi_file.status_code)
                  + " skip")
            continue
        print("Success: " + _openapi_yaml)

        
        # make dir "openapi" if not exist
        # use host name as file name, put all openapi files in the subfolder "openapi"
        _openapi_file_name = _openapi.split("/")[2] + ".yaml"
        with open("openapi/" + _openapi_file_name, "w") as f:
            f.write(_openapi_file.text)
    except Exception as e:
        print(e)
        continue
