import json
import logging
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

'''
LLM_CONFIG = {
    "custom_prompt": config["ai"]["prompt"],
    "model": config["ai"]["model"],
    "temperature": config["ai"]["temperature"],
    "api_key": SECRET_KEYS.pop("GEMINI_API_KEY"),
}
'''
# llm_outputs, llm_stats = hinge(llm_config)
# llm_outputs = {title: , content: , categories:}
# llm_stats = {input_tokens:, thoughts_tokens:, output_tokens:}

class BlogPost(BaseModel):
    title: str = Field(description="ブログのタイトル。")
    content: str = Field(
        description="ブログの本文（マークダウン形式）。"
    )
    categories: List[str] = Field(description="カテゴリー一覧", max_length=4)

class LlmFee(ABC):
    def __init__(self, model:str):
        self.model = model

    @abstractmethod
    @property
    def fees(self):
        pass
    @abstractmethod
    @property
    def model_list(self):
        pass

    @abstractmethod
    def calculate(self, tokens:int, token_type:str) -> float:
        pass

class GeminiFee(LlmFee):
    '''2025/12/09現在'''
    _fees = {
        "gemini-2.5-flash": {"input": 0.03, "output": 2.5},  # $per 1M tokens 
        "gemini-2.5-pro": {
            "under_0.2M": {"input": 1.25, "output": 10.00},
            "over_0.2M": {"input": 2.5, "output": 15.0},
        }
    }
    _model_list = ["gemini-2.5-flash", "gemini-2.5-pro"]

    @property
    def fees(self):
        return self._fees
    
    @property
    def model_list(self):
        return self._model_list        

    def calculate(self, tokens, token_type) -> float:
        model = self.model
        token_type = "output" if token_type == "thoughts" else token_type
        if self.model not in self.model_list:
            logger.warning("料金表に登録されていないモデルです")
            logger.warning("'gemini-2.5-proの料金で試算します")
            model = "gemini-2.5-pro"
        if model == "gemini-2.5-flash":
            dollar_per_1M_tokens = tokens * self.fees[self.model][token_type]
        elif model == "gemini-2.5-pro":
            base_fee = self.fees["gemini-2.5-pro"]
            if tokens <= 200000:
                dollar_per_1M_tokens = base_fee["under_0.2M"][token_type]
            else:
                 dollar_per_1M_tokens = base_fee["over_0.2M"][token_type]
            
        return dollar_per_1M_tokens * tokens / 1000000

class DeepseekFee(LlmFee):
    _fees = {"input(cache_hit)": 0.028, "input(cache_miss)":0.28, "output": 0.42}
    _model_list = ["Deepseek-chat", "Deepseek-reasoner"]

    @property
    def fees(cls):
        return cls._fees

    @property
    def model_list(cls):
        return cls._model_list

    def calculate(self, tokens, token_type):
        token_type = "output" if token_type == "thoughts" else token_type
        if token_type == "output":
            dollar_per_1M_tokens = self.fees["output"]
        else:
            dollar_per_1M_tokens = self.fees["input(cache_miss)"]
        
        return dollar_per_1M_tokens * tokens / 1000000

            

class ConversationalAi(ABC):
    def __init__(self, model:str, api_key:str, conversation:str, prompt: str,temperature:float = 1.1):
        self.model = model or "gemini-2.5-flash"
        self.api_key = api_key
        self.temperature = temperature        
        self.company_name = "Google" if self.model.startswith("gemini") else "Deepseek"
        STATEMENT = f"またその最後には、「この記事は {self.model} により自動生成されています」と目立つように注記してください。"    
        self.prompt = prompt + STATEMENT+ "\n\n" + conversation

    @abstractmethod
    def get_summary(self) -> tuple[dict, dict]:
        pass

    def handle_server_error(self, i, max_retries):
        if i < max_retries - 1:
            logger.warning(
                f"{self.company_name}の計算資源が逼迫しているようです。{5 * (i + 1)}秒後にリトライします。"
            )
            time.sleep(5 * (i + 1))
        else:
            logger.warning(f"{self.company_name}は現在過負荷のようです。少し時間をおいて再実行する必要があります。")
            logger.warning("実行を中止します。")
            sys.exit(1)

    def handle_client_error(self, e:BaseException):
        logger.error("エラー：APIレート制限。")
        logger.error("詳細はapp.logを確認してください。実行を中止します。")
        logger.info(f"詳細: {e}")
        sys.exit(1)

    def handle_unexpected_error(self, e:BaseException):
        logger.error("要約取得中に予期せぬエラー発生。詳細はapp.logを確認してください。")
        logger.error("実行を中止します。")
        logger.info(f"詳細: {e}")
        raise

    def check_response(self, response_text):        
        required_keys = {"title", "content", "categories"}
        try:
            data = json.loads(response_text)
            if set(data.keys()) == required_keys:
                logger.warning("Deepseekが構造化出力に成功")
        except Exception:
            logger.error(f"{self.model}が構造化出力に失敗。")
            
            output_path = Path.cwd() / "outputs"
            output_path.mkdir(exist_ok=True)
            file_path = output_path / "__summary.txt"
            file_path.write_text(response_text, encoding="utf-8")

            logger.error(f"{file_path}へ出力を保存しました。")
            sys.exit(1)

        return data
    
class GeminiClient(ConversationalAi):
    def get_summary(self):
        from google import genai
        from google.genai import types
        from google.genai.errors import ClientError, ServerError

        logger.warning("Geminiからの応答を待っています。")
        logger.debug(f"APIリクエスト中。APIキー: ...{self.api_key[-5:]}")

        # api_key引数なしでも、環境変数"GEMNI_API_KEY"の値を勝手に参照するが、可読性のため代入
        client = genai.Client(api_key=self.api_key)

        max_retries = 3
        for i in range(max_retries):
            # generate_contentメソッドは内部的にHTTPレスポンスコード200以外の場合は例外を発生させる
            try:
                response = client.models.generate_content(  # リクエスト
                    model=self.model,
                    contents=self.prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        response_mime_type="application/json",  # 構造化出力
                        response_json_schema=BlogPost.model_json_schema(),
                    ),
                )
                print("Geminiによる要約を受け取りました。")
                break
            except ServerError:
                super().handle_server_error(i, max_retries)
            except ClientError as e:
                super().handle_client_error(e)
            except Exception as e:
                super().handle_unexpected_error(e)

        data = super().check_response(response.text)

        stats = {
            "output_letter_count": len(response.text),
            "input_tokens": response.usage_metadata.prompt_token_count,
            "thoughts_tokens": response.usage_metadata.thoughts_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count,
        }

        return data, stats
    
class DeepseekClient(ConversationalAi):
    def get_summary(self) -> tuple[dict, dict]:
        from openai import OpenAI

        logger.warning("Deepseekからの応答を待っています。")
        logger.debug(f"APIリクエスト中。APIキー: ...{self.api_key[-5:]}")

        client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

        max_retries = 3
        for i in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    messages=[{"role":"user", "content":self.prompt}],
                    response_format={'type': 'json_object'},
                    stream=False
                )
                break
            except Exception as e:
                # https://api-docs.deepseek.com/quick_start/error_codes
                if any(code in str(e) for code in [500, 502, 503]):
                    super().handle_server_error(i, max_retries)
                elif "429" in str(e):
                    logger.error("APIレート制限。しばらく経ってから再実行してください。")
                    raise
                elif "401" in str(e):
                    logger.error("エラー：APIキーが誤っているか、入力されていません。")
                    logger.error(f"実行を中止します。詳細：{e}")
                    sys.exit(1)
                elif "402" in str(e):
                    logger.error("残高が不足しているようです。アカウントを確認してください。")
                    logger.error(f"実行を中止します。詳細：{e}")
                    sys.exit(1)
                elif "422" in str(e):
                    logger.error("リクエストに無効なパラメータが含まれています。設定を見直してください。")
                    logger.error(f"実行を中止します。詳細：{e}")
                    sys.exit(1)
                else:
                    super().handle_unexpected_error(e)

        generated_text = response.choices[0].message.content   
        data = super().check_response(generated_text)

        thoughts_tokens = getattr(response.usage.completion_tokens_details,"reasoning_tokens", 0)
        stats = {
            "output_letter_count": len(generated_text),
            "prompt_tokens": response.usage.prompt_tokens,
            "thoughts_tokens": thoughts_tokens,
            "output_tokens": response.usage.completion_tokens - thoughts_tokens,
        }

        return data, stats
