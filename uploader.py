import os
import xml.etree.ElementTree as ET
from pathlib import Path

import xmltodict
import yaml
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv(override=True)
config_path = Path("config.yaml")
config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

DEBUG = config["other"]["debug"].lower() in ("true", "1", "t")


entry_xml = r"""<?xml version="1.0" encoding="utf-8"?>

<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>初めての投稿</title>
  <author><name>name</name></author>
  <content type="text/plain">
    pythonでOAuth認証を行いAPIで送信し投稿しています。これからプログラミングの学習記録を自動投稿していく予定。
  </content>
  <category term="Scala" />
  <app:control>
    <app:draft>yes</app:draft>
    <app:preview>no</app:preview>
  </app:control>
</entry>"""


def xml_unparser(title, content, author="", category: dict = {}) -> str:
    # 実装予定
    ROOT = ET.Element(
        "entry",
        attrib={
            "xmlns": "http://www.w3.org/2005/Atom",
            "xmlns:app": "http://www.w3.org/2007/app",
        },
    )

    TITLE = ET.SubElement(ROOT, "title")
    TITLE.text = title

    AUTHOR = ET.SubElement(ROOT, "author")
    NAME = ET.SubElement(AUTHOR, "name")
    NAME.text = author
    CONTENT = ET.SubElement(ROOT, "content", attrib={"type": "text/x-markdown"})
    CONTENT.text = content
    ET.SubElement(ROOT, "category", attrib=category)
    CONTROL = ET.SubElement(ROOT, "app:control")
    DRAFT = ET.SubElement(CONTROL, "app:draft")
    DRAFT.text = "yes"
    PREVIEW = ET.SubElement(CONTROL, "app:preview")
    PREVIEW.text = "no"

    return ET.tostring(ROOT, encoding="unicode")


def uploader(entry_xml: str = None):
    URL = os.getenv(
        "HATENA_BASE_URL", None
    ).strip()  # https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/

    # 環境変数を読み込み
    CONSUMER_KEY = os.getenv("HATENA_CONSUMER_KEY", None).strip()
    CONSUMER_SECRET = os.getenv("HATENA_CONSUMER_SECRET", None).strip()
    ACCESS_TOKEN = os.getenv("HATENA_ACCESS_TOKEN", None).strip()
    ACCESS_TOKEN_SECRET = os.getenv("HATENA_ACCESS_TOKEN_SECRET", None).strip()

    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )

    response = oauth.post(
        URL, data=entry_xml, headers={"Content-Type": "application/xml; charset=utf-8"}
    )

    return xmltodict.parse(response.text)["entry"]  # 辞書型で出力


if __name__ == "__main__":
    if DEBUG:
        entry_xml = xml_unparser(
            "タイトル", "本文のテスト", "Unknown", {"term": "python"}
        )
        data = uploader(entry_xml)  # 辞書型

        print(
            f"投稿に成功しました：\n{'-' * 50}\nタイトル：{data["title"]}\n著者：{data["author"]["name"]}\n本文：\n{data["content"]["#text"]}"
        )
