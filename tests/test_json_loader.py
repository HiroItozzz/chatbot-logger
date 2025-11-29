from pathlib import Path

import json_loader as jl

sample_path = Path(
    r"e:\Downloads\Claude-ターミナルのグラフィックスドライバー問題 (2).json"
)


def test_json_loader():
    result = jl.json_loader(sample_path)
    assert isinstance(result, str)
    assert len(result) > 0


if __name__ == "__main__":
    a = jl.json_loader(sample_path)
    print(a[:200])
