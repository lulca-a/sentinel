import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

url = "https://api-redemet.decea.mil.br/produtos/radar/maxcappi"
params = {
    "api_key": API_KEY
}

def get_radar(url, params):
    resp = requests.get(url, params=params)

    print("STATUS:", resp.status_code)
    print("TEXT:", resp.text)
    resp = requests.get(url, params=params)

    print(resp.status_code)
    print(resp.text)
    print(API_KEY)
    try:
        data = resp.json()
        print("JSON:", data)
        return data.get('data')
    except Exception as e:
        print("ERRO JSON:", e)
        return None
    
import json

data = get_radar(url, params)

print(json.dumps(data, indent=2))