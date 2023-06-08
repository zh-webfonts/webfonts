import sys
import yaml
import requests
import time
import json
import re

def open_github_issue(font_name, version_number, auth_token):
    issue_title = f"{font_name} has a new version {version_number}"
    issue_url = "https://api.github.com/repos/zh-webfonts/webfonts/issues"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": issue_title
    }

    response = requests.post(issue_url, headers=headers, json=data)

    try:
        response.raise_for_status()
        print(f"Issue opened successfully: {issue_title}")
    except requests.HTTPError as e:
        print(f"Error occurred while opening the issue: {e}")

def update_published_on_and_version(auth_token):
    with open('font-tracer.yml', 'r') as file:
        data = yaml.safe_load(file)

    for item in data['fonts']:
        print()  # Print blank line before each iteration

        if item['source']['type'] == 'npm':
            package_name = item['source']['value']
            package_name_parts = package_name.split('/')
            if len(package_name_parts) == 1:  # Non-scoped package
                scope = ''
                package = package_name_parts[0]
            else:  # Scoped package
                scope = package_name_parts[0]
                package = package_name_parts[1]

            api_url = f'https://registry.npmjs.org/{scope}/{package}'

            print(f"Accessing NPM API: {api_url}")
            response = requests.get(api_url)

            try:
                response.raise_for_status()
                package_info = response.json()
                latest_version = package_info['dist-tags']['latest']
                published_time = package_info['time'].get(latest_version, 0)
                if not item['version'].get('published_on') or published_time > item['version']['published_on']:
                    item['version']['version_number'] = latest_version
                    item['version']['published_on'] = published_time
                    item['version']['changed'] = True
                    print(f"Updated '{item['name']}' - Version: {latest_version}, Published On: {published_time}")
                    open_github_issue(item['name'], latest_version, auth_token)
                else:
                    item['version']['changed'] = False
                    print(f"No update available for '{item['name']}' - Version: {latest_version}, Published On: {published_time}")
            except (requests.HTTPError, json.JSONDecodeError) as e:
                print(f"Error occurred while retrieving package info for '{item['name']}' from NPM: {e}")

        elif item['source']['type'] == 'github':
            repo_url = item['source']['value']
            repo_url_parts = repo_url.split('/')
            repo_owner = repo_url_parts[-2]
            repo_name = repo_url_parts[-1]

            api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest'

            print(f"Accessing GitHub API: {api_url}")
            response = requests.get(api_url)

            try:
                response.raise_for_status()
                latest_release = response.json()
                latest_version = latest_release['tag_name']
                published_time = latest_release['published_at']
                if not item['version'].get('published_on') or published_time > item['version']['published_on']:
                    item['version']['version_number'] = latest_version
                    item['version']['published_on'] = published_time
                    item['version']['changed'] = True
                    print(f"Updated '{item['name']}' - Version: {latest_version}, Published On: {published_time}")
                    open_github_issue(item['name'], latest_version, auth_token)
                else:
                    item['version']['changed'] = False
                    print(f"No update available for '{item['name']}' - Version: {latest_version}, Published On: {published_time}")
            except (requests.HTTPError, json.JSONDecodeError) as e:
                print(f"Error occurred while retrieving release info for '{item['name']}' from GitHub: {e}")

        item['version']['last_checked'] = int(time.time())
        print(f"Rewriting 'last_checked' for '{item['name']}' to current time: {item['version']['last_checked']}")

    print()  # Print blank line after each iteration

    with open('font-tracer.yml', 'w') as file:
        yaml.dump(data, file)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Please provide the GitHub authentication token as a command-line argument.")
        print("Usage: python script.py <auth_token>")
        sys.exit(1)

    auth_token = sys.argv[1]
    update_published_on_and_version(auth_token)
