"""OpenDev API 统一封装：文本 / JSON / 生图，超时+重试+容错解析。

全部走 requests（少一个 openai SDK 依赖），代理由 config.py import 时设置。
"""
from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path

import requests

from config import settings

_TIMEOUT = 90          # 文本请求超时（glm-5.3-flash 实测 3-10s，留裕量）
_IMG_TIMEOUT = 180     # 生图超时（实测 25s/张，高峰留裕量）

# response_format=json_object 是否可用（首次 400 后永久关闭，探测一次）
_json_mode_supported: bool | None = None


class LLMError(Exception):
    """LLM 调用失败（网络/限流/解析均不出去）。"""


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }


def _post(url: str, payload: dict, timeout: int) -> dict:
    resp = requests.post(url, headers=_headers(), json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise LLMError(f"API {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def chat_text(system: str, user: str, *, model: str | None = None,
              temperature: float = 0.7, retries: int = 1) -> str:
    """普通文本对话。"""
    global _json_mode_supported
    model = model or settings.text_model
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            data = _post(f"{settings.base_url}/chat/completions", payload, _TIMEOUT)
            return data["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, LLMError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise LLMError(f"文本生成失败（{model}）: {last_err}")


def extract_json(text: str) -> dict:
    """三层容错解析：直接 loads → 剥```围栏 → 平衡括号扫描。"""
    text = text.strip()
    # 1) 直接尝试
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 2) 剥 markdown 围栏（glm 爱包 ```json ... ```）
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except json.JSONDecodeError:
            pass
    # 3) 首个 { 起平衡括号扫描到闭合
    start = text.find("{")
    if start >= 0:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
    raise ValueError("无法从模型输出中解析出 JSON")


def chat_json(system: str, user: str, *, model: str | None = None,
              retries: int = 2) -> dict:
    """结构化输出：response_format 尝试（不支持的网关自动降级）→ 容错解析 → 带错误重试。"""
    global _json_mode_supported
    model = model or settings.text_model
    base_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.5,
    }
    last_err: Exception | None = None
    messages = list(base_payload["messages"])
    for attempt in range(retries + 1):
        payload = dict(base_payload, messages=messages)
        if _json_mode_supported is not False:
            payload["response_format"] = {"type": "json_object"}
        try:
            data = _post(f"{settings.base_url}/chat/completions", payload, _TIMEOUT)
            content = data["choices"][0]["message"]["content"]
            return extract_json(content)
        except LLMError as e:
            # response_format 不被网关支持 → 关闭后重试（只探测一次）
            if _json_mode_supported is None and "400" in str(e):
                _json_mode_supported = False
                last_err = e
                continue
            last_err = e
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            last_err = e
            # 带着解析错误让模型自我修正
            messages = list(base_payload["messages"]) + [
                {"role": "assistant", "content": "(上次输出无法解析为JSON)"},
                {"role": "user", "content":
                    f"你上次的输出无法解析为 JSON，错误：{e}。请重新输出，"
                    "只输出一个合法的 JSON 对象，不要任何解释和 markdown 围栏。"},
            ]
        time.sleep(1.5 * (attempt + 1))
    raise LLMError(f"JSON 生成失败（{model}）: {last_err}")


def gen_image(prompt: str, out_path: Path, *, size: str | None = None,
              retries: int = 2) -> Path:
    """文生图：b64_json 优先（避免 URL 过期/二次下载），URL 兜底。约 25s/张。"""
    payload = {
        "model": settings.image_model,
        "prompt": prompt,
        "size": size or settings.image_size,
    }
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            data = _post(f"{settings.base_url}/images/generations", payload, _IMG_TIMEOUT)
            item = data["data"][0]
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if item.get("b64_json"):
                out_path.write_bytes(base64.b64decode(item["b64_json"]))
            elif item.get("url"):
                img = requests.get(item["url"], timeout=60)
                img.raise_for_status()
                out_path.write_bytes(img.content)
            else:
                raise LLMError("生图返回里既无 b64_json 也无 url")
            return out_path
        except (requests.RequestException, KeyError, IndexError, LLMError) as e:
            last_err = e
            time.sleep(3 * (attempt + 1))
    raise LLMError(f"生图失败（{settings.image_model}）: {last_err}")


def healthcheck() -> tuple[bool, str]:
    """启动探活：8 秒超时 ping 一条最小对话。返回 (ok, 消息)。"""
    try:
        data = _post(
            f"{settings.base_url}/chat/completions",
            {"model": settings.text_model,
             "messages": [{"role": "user", "content": "回复OK"}],
             "max_tokens": 10},
            timeout=8,
        )
        return True, f"API 正常（{data['choices'][0]['message']['content'].strip()[:20]}）"
    except Exception as e:  # noqa: BLE001 探活不抛
        return False, f"API 不可用：{str(e)[:120]}，可切换演示模式"
