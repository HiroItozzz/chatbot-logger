import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import load_dotenv
from google import genai
from json_loader import json_loader
from pydantic import BaseModel, Field

load_dotenv(override=True)
config_path = Path(__file__).parent.parent / Path("config.yaml")
config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

INPUT_PATH = Path(
    r"E:\Dev\Projects\chatbot-logger\sample\Claude-Git LF!CRLF line ending issues across platforms (1).json"
)
conversation = INPUT_PATH.read_text()

model = config["ai"]["model"]
default_prompt = config["ai"]["prompt"]
level = config["ai"]["thoughts_level"]
prompt = default_prompt + conversation


#### format
"""def xml_unparser(
    title: str,
    content: str,
    categories: list | None = None,
    author: str | None = None,
    updated: datetime | None = None,
) -> str:
"""

class BlogPost(BaseModel):
    title: str = Field(description="ブログのタイトル。")
    content: str = Field(description="ブログの本文（マークダウン形式）")
    categories: list[str] = Field(description="カテゴリー一覧")
    author: None
    updated: None


client = genai.Client()

response = client.models.generate_content(
    model=model,
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_json_schema": BlogPost.model_json_schema(),
    },
)

post = BlogPost.model_validate_json(response.text)
data = post.model_dump()
with open("sample/structured_output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
