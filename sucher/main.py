import os
import requests
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = FastAPI()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

query_counter = {}  # stores {user_ip: (count, reset_time)}

GOOGLE_CX = os.getenv("GOOGLE_CX")  # get cx from .env

def fetch_results(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"# debug
    response = requests.get(url)
    
    print("STATUS CODE:", response.status_code)  # debug
    print("RAW RESPONSE:", response.text)  # debug

    if response.status_code == 200:
        data = response.json()
        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "title": item.get("title", "No Title"),
                    "url": item.get("link", "#"),
                    "desc": item.get("snippet", "No description")
                })
        return results
    return []



@app.get("/search")
def search(q: str, user_ip: str):  # user_ip to track requests
    now = datetime.utcnow()
    
    if user_ip in query_counter:
        count, reset_time = query_counter[user_ip]
        if now < reset_time:
            if count >= 99:
                raise HTTPException(status_code=429, detail="Daily limit of 99 searches reached")
            query_counter[user_ip] = (count + 1, reset_time)
        else:
            query_counter[user_ip] = (1, now + timedelta(days=1))
    else:
        query_counter[user_ip] = (1, now + timedelta(days=1))

    results = fetch_results(q)
    return {"results": results if results else "No results found"}
