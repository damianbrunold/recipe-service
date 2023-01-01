import json
import os
import sys

import requests

config = {"current-profile": "default", "profiles": {"default": {}}}
profile = config["profiles"][config["current-profile"]]


def call_api(method, url, payload=None):
    headers = {
        "Authorization": f"Bearer {profile['token']}",
    }
    if payload:
        payload = json.loads(payload)
    if method == "get":
        response = requests.get(url)
        print(json.dumps(response.json(), indent=2))
    elif method == "add":
        response = requests.post(url, json=payload, headers=headers)
        print(json.dumps(response.json(), indent=2))
    elif method == "update":
        response = requests.patch(url, json=payload, headers=headers)
        print(json.dumps(response.json(), indent=2))
    elif method == "delete":
        response = requests.delete(url, headers=headers)
        print(json.dumps(response.json(), indent=2))


def configure():    
    print(f"Profile {config['current-profile']}")
    url = input(f"Enter API URL ({profile.get('url', '-')}): ")
    if url:
        profile["url"] = url
    token = input(f"Enter token ({profile.get('token', '-')[0:10] + '...'}): ")
    if token:
        profile["token"] = token
    config["profiles"][config["current-profile"]] = profile
    with open(".call-config", "w") as outfile:
        outfile.write(json.dumps(config, indent=2))


def set_profile():
    new_profile = input(f"Enter profile name ({config['current-profile']}): ")
    config["current-profile"] = new_profile
    if new_profile not in config["profiles"]:
        config["profiles"][new_profile] = {}
    with open(".call-config", "w") as outfile:
        outfile.write(json.dumps(config, indent=2))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ["help", "--help", "-h"]:
        print("python call.py set-profile")
        print("python call.py configure")
        print("python call.py recipe list [<page>]")
        print("python call.py recipe get [<recipe_id>]")
        print("python call.py recipe add <json-data>")
        print("python call.py recipe update <recipe_id> <json-data>")
        print("python call.py recipe delete <recipe_id>")
        print("python call.py menu get [<recipe_id>] [<page>]")
        print("python call.py menu add <json-data>")
        print("python call.py menu update <recipe_id> <json-data>")
        print("python call.py menu delete <recipe_id>")
        exit(0)

    if (
        not os.path.exists(".call-config") 
        and not args[0] in ["configure", "set-profile"]
    ):
        print("Call configure first")
        exit(0)

    if os.path.exists(".call-config"):
        with open(".call-config") as infile:
            config = json.loads(infile.read())
            profile = config["profiles"][config["current-profile"]]

    if args[0] == "configure":
        configure()
    elif args[0] == "set-profile":
        set_profile()
    else:
        entity = args[0]
        if args[1] == "list":
            url = f"{profile['url']}/{entity}"
            if len(args) > 2:
                url += "?page=" + args[2]
            call_api("get", url)
        elif args[1] == "get":
            url = f"{profile['url']}/{entity}/{args[2]}"
            call_api("get", url)
        elif args[1] == "add":
            url = f"{profile['url']}/{entity}"
            payload = args[2]
            call_api("add", url, payload)
        elif args[1] == "update":
            url = f"{profile['url']}/{entity}/{args[2]}"
            payload = args[3]
            call_api("update", url, payload)
        elif args[1] == "delete":
            url = f"{profile['url']}/{entity}/{args[2]}"
            call_api("delete", url)
