import os
from pathlib import Path
import json, csv
from datetime import datetime, timedelta 
from dotenv import load_dotenv
import yaml
from google import genai
from google.genai import types

from loader import json_formatter
from ai_client import summary_from_gemini



load_dotenv()
config_path = Path('config.yaml')
config = yaml.safe_load(config_path.read_text(encoding='utf-8'))


API_KEY = os.getenv('GEMINI_API_KEY', "").strip()

PROMPT = config['ai']['prompt']
MODEL = config['ai']['model']
LEVEL = config['ai']['thoughts_level']

DEBUG = config['other']['debug'].lower() in ("true", "1", "t")


if __name__ == "__main__":
    
    ### loader.pyで自動取得に変更予定 ###
    INPUT_DIR = ""

    INPUT_PATH = Path(r"E:\Dev\Projects\chatbot-logger\sample\Claude-Git LF!CRLF line ending issues across platforms (1).json")
    ####################


    with open (INPUT_PATH, encoding="utf-8") as f:
        raw_data = json.load(f)

    base_text = "\n".join(json_formatter(raw_data))

    output_dir = Path(config['paths']['output_dir'].strip())
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / (INPUT_PATH.stem + '.txt')

    output_path.write_text(base_text, encoding="utf-8")  # AIに投げるテキストをバックアップ

    if DEBUG:
        print(base_text)
        exit()

    output_text, input_token, output_token = summary_from_gemini(base_text, API_KEY, prompt=PROMPT, model=MODEL, thoughts_level=LEVEL)



