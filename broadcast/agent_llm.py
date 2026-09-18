"""LLM 客户端封装 —— 薄薄一层：进 messages，出文本 + token 用量。

默认接 DeepSeek（OpenAI 兼容协议，价格便宜、国内直连不用挂梯子）。
换其他 OpenAI 兼容服务（Kimi / 通义 / 自建网关等）只需要改三个环境变量，
不用碰这个文件：

    LLM_API_KEY   必填
    LLM_BASE_URL  默认 https://api.deepseek.com
    LLM_MODEL     默认 deepseek-chat
"""
import os
from openai import OpenAI

_client = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ.get("LLM_API_KEY", ""),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com"),
        )
    return _client


MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")


class Usage:
    """统一 usage 字段名，供 summarize.py / run_broadcast.py 做 token 统计——
    这两个数字（input_tokens）正是全项目 --naive 对比要量出来的东西。"""

    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class Response:
    def __init__(self, text: str, usage: Usage):
        self.text = text
        self.usage = usage


def complete(messages, system=None, max_tokens=1024) -> Response:
    """一次模型调用。system 单独传入，内部拼成 system role 消息。"""
    msgs = ([{"role": "system", "content": system}] if system else []) + list(messages)
    resp = client().chat.completions.create(model=MODEL, max_tokens=max_tokens, messages=msgs)
    usage = Usage(resp.usage.prompt_tokens, resp.usage.completion_tokens)
    text = resp.choices[0].message.content or ""
    return Response(text.strip(), usage)


def text_of(resp: Response) -> str:
    return resp.text
