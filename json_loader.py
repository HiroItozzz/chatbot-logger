import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")


def json_loader(path: Path) -> list:
    AI_LIST = ["Claude", "Gemini", "ChatGPT"]

    ai_name = next((p for p in AI_LIST if path.name.startswith(p)), "Unknown AI")

    data_text = path.read_text(encoding="utf-8")
    data = json.loads(data_text)
    dates_meta = data["metadata"]["dates"]
    format_meta = "%m/%d/%Y %H:%M:%S"

    created_datetime = datetime.strptime(
        (dates_meta.get("created")), format_meta
    )  # start time of the chat
    updated_datetime = datetime.strptime(
        (dates_meta.get("updated")), format_meta
    )  # updated time of the chat

    latest_datetime = created_datetime

    logs = []

    for message in data["messages"]:
        timestamp = message.get("time")
        text_datetime = datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S")
        time_diff = text_datetime - latest_datetime

        # Skip messages from previous days unless more than an hour has passed
        if not DEBUG:
            if text_datetime.date() != latest_datetime.date():
                if time_diff > timedelta(hours=1):
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

        text = message.get("say")

        logs.append(f"{timestamp} \nagent: {agent}\n {text} \n\n {'-' * 50}\n")

        latest_datetime = text_datetime

    return "\n".join(logs)


if __name__ == "__main__":

    INPUT_PATH = Path(
        r"E:\Dev\Projects\chatbot-logger\sample\Claude-Git LF!CRLF line ending issues across platforms (1).json"
    )
    print(json_loader(INPUT_PATH)[:200])
