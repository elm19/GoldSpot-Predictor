import requests

url = "https://elm19.pythonanywhere.com/"
response = requests.get(url)

# Check status and print response
if response.status_code == 200:
    print("Response JSON:", response)
else:
    print(f"Request failed with status code {response.status_code}")
