"""托摆配置加载：.env 读取 + 路径校验 + 代理环境变量。

import config 即完成代理设置（llm_client 的 requests 会经 trust_env 走代理）。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def _load_dotenv(path: Path) -> dict[str, str]:
    """极简 .env 解析（少一个 python-dotenv 依赖）。"""
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


_raw = _load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Settings:
    base_url: str = _raw.get("OPENAI_BASE_URL", "https://api.openai-next.com/v1")
    api_key: str = _raw.get("OPENAI_API_KEY", "")
    proxy: str = _raw.get("HTTP_PROXY", "")
    no_proxy: str = _raw.get("NO_PROXY", "localhost,127.0.0.1")
    text_model: str = _raw.get("TEXT_MODEL", "glm-5.3-flash")
    image_model: str = _raw.get("IMAGE_MODEL", "gpt-image-2")
    image_size: str = _raw.get("IMAGE_SIZE", "1024x1024")
    goofish_exe: str = _raw.get("GOOFISH_EXE", "")
    py_main: str = _raw.get("PY_MAIN", "")
    render_xhs: str = _raw.get("RENDER_XHS", "")
    xhs_theme: str = _raw.get("XHS_THEME", "sketch")
    parallel_images: int = int(_raw.get("PARALLEL_IMAGES", "1") or 1)
    enable_video: bool = _raw.get("ENABLE_VIDEO", "false").lower() == "true"
    video_model: str = _raw.get("VIDEO_MODEL", "sora-2")
    output_dir: Path = PROJECT_ROOT / "output"
    examples_dir: Path = PROJECT_ROOT / "examples"
    prompts_dir: Path = PROJECT_ROOT / "prompts"

    def validate(self) -> list[str]:
        """返回缺失项中文报错列表（UI 启动时展示）。"""
        problems = []
        if not self.api_key:
            problems.append("缺少 OPENAI_API_KEY：请复制 .env.example 为 .env 并填入")
        if self.goofish_exe and not Path(self.goofish_exe).exists():
            problems.append(f"goofish.exe 路径不存在：{self.goofish_exe}（闲鱼上架将不可用）")
        if self.py_main and not Path(self.py_main).exists():
            problems.append(f"PY_MAIN 路径不存在：{self.py_main}（小红书卡片将不可用）")
        if self.render_xhs and not Path(self.render_xhs).exists():
            problems.append(f"render_xhs.py 路径不存在：{self.render_xhs}（小红书卡片将不可用）")
        return problems


settings = Settings()

# import 即设置代理（对本进程所有 requests/openai 调用生效）
if settings.proxy:
    os.environ.setdefault("HTTP_PROXY", settings.proxy)
    os.environ.setdefault("HTTPS_PROXY", settings.proxy)
    os.environ.setdefault("http_proxy", settings.proxy)
    os.environ.setdefault("https_proxy", settings.proxy)
    os.environ["NO_PROXY"] = settings.no_proxy
    os.environ["no_proxy"] = settings.no_proxy
