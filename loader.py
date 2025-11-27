import os
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime as dt
from datetime import timedelta as td


sample = "sample.json"
PATH = Path('.') / sample

AI_LIST = ["Claude", "ChatGPT", "Deepseek", "Gemini", "Grok"]

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")




def json_formatter(data: dict) -> list:
    logs = []

    dates_meta = data["metadata"]["dates"]
    format_meta = '%m/%d/%Y %H:%M:%S'

    created_datetime = dt.strptime((dates_meta.get("created")), format_meta)    # start time of the chat
    updated_datetime = dt.strptime((dates_meta.get("updated")), format_meta)    # updated time of the chat

    ai_name = "Unknown AI"
    for name in AI_LIST:
        if name.lower() in data["metadata"].get("powered_by").lower():
            ai_name = name
            break

    latest_datetime = created_datetime

    for message in data["messages"]:
        text_datetime = dt.strptime(message.get("time"), '%Y/%m/%d %H:%M:%S')
        time_diff = text_datetime - latest_datetime

        # Skip messages from previous days unless more than an hour has passed
        if not DEBUG:
            if text_datetime.date() != latest_datetime.date():   
                if time_diff.seconds // 3600 > 1:
                    latest_datetime = text_datetime
                    continue

        if message.get("role") == "Prompt":
            agent = "You"
        elif message.get("role") == "Response":
            agent = ai_name        
        else:
            agent = message.get("role")
            if DEBUG:
                print(f"Detected agent other than You and {ai_name}: {agent}")
        
        text_time = text_datetime.strftime('%H:%M:%S')
        text = message.get("say")

        logs.append(f"{text_time} 'agent': {agent}\n 'text': {text}\n)")

        latest_datetime = text_datetime

    return logs

if __name__ == "__main__":
    with open (PATH, encoding="utf-8") as f:
        raw_data = json.load(f)

    output_texts = "\n".join(json_formatter(raw_data))
    print(output_texts)
