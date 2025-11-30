from pathlib import Path

import yaml
from dotenv import load_dotenv
from uploader import hatena_uploader, xml_unparser

load_dotenv(override=True)
config_path = Path("config.yaml")
config = yaml.safe_load(config_path.read_text(encoding="utf-8"))


def test_hatena_uploader():
    result = hatena_uploader()
    assert result
    assert len(result.keys())
