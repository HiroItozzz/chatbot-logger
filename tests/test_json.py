from pathlib import Path

import json_loader as jl

INPUT_PATH = Path(
    r"E:\Dev\Projects\chatbot-logger\sample\Claude-Git LF!CRLF line ending issues across platforms (1).json"
)

a = jl.json_loader(INPUT_PATH)
print(a[:200])
