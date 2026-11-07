import re
from pathlib import Path


def init_project_context():
    """动态导入父模块"""
    import os
    import sys

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../..")
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


init_project_context()

from core.utils.config import ConfigManager
from core.utils.file import get_model_file_path
from core.utils.logger import logger


def should_generate_keywords():
    """Return whether keyword generation should run."""
    import os

    xiaozhi_enabled = os.environ.get("XIAOZHI_ENABLE", "").lower() in ("1", "true", "yes")
    # 兼容 OPENCLAW_ENABLE (新) 和 OPENCLAW_ENABLED (旧)
    openclaw_env = os.environ.get("OPENCLAW_ENABLE") or os.environ.get("OPENCLAW_ENABLED") or ""
    openclaw_enabled = openclaw_env.lower() in ("1", "true", "yes")
    openai_enabled = os.environ.get("OPENAI_ENABLE", "").lower() in (
        "1",
        "true",
        "yes",
    )
    qwenpaw_enabled = os.environ.get("QWENPAW_ENABLE", "").lower() in (
        "1",
        "true",
        "yes",
    )

    if (
        not xiaozhi_enabled
        and not openclaw_enabled
        and not openai_enabled
        and not qwenpaw_enabled
    ):
        return False, "XIAOZHI_ENABLE, OPENCLAW_ENABLE/OPENCLAW_ENABLED, OPENAI_ENABLE and QWENPAW_ENABLE are all disabled"

    return True, ""


def get_args():
    config = ConfigManager.instance()
    tokens_type = "cjkchar+bpe"
    tokens = get_model_file_path("tokens.txt")
    bpe_model = get_model_file_path("bpe.model")
    output = get_model_file_path("keywords.txt")
    keywords = config.get_app_config("wakeup.keywords", [])
    texts = [f"{keyword.upper()}" for keyword in keywords]
    return locals()


def main():
    should_run, reason = should_generate_keywords()
    if not should_run:
        logger.debug(f"Keyword generation skipped: {reason}", module="KWS")
        return 0

    required_files = [
        get_model_file_path("tokens.txt"),
        get_model_file_path("bpe.model"),
    ]
    missing_files = [path for path in required_files if not Path(path).is_file()]
    if missing_files:
        logger.debug(
            "Keyword generation failed: missing model files: "
            f"{', '.join(missing_files)}",
            module="KWS",
        )
        return 1

    from sherpa_onnx import text2token

    args = get_args()
    encoded_texts = text2token(
        args["texts"],
        tokens=args["tokens"],
        tokens_type=args["tokens_type"],
        bpe_model=args["bpe_model"],
    )

    # 针对英文单词及中文多音/谐音词在 Zipformer 声学模型下的加固
    extra_phonetic_keywords = [
        ("小艺小艺", "小艺"),
        ("你好小艺", "小艺"),
        ("小易小易", "小艺"),
        ("你好小易", "小艺"),
        ("小意小意", "小艺"),
        ("你好小意", "小艺"),
        ("小翼小翼", "小艺"),
        ("你好小翼", "小艺"),
        ("小义小义", "小艺"),
        ("你好小义", "小艺"),
        ("肥鲸肥鲸", "小艺"),
        ("肥金肥金", "小艺"),
        ("肥京肥京", "小艺"),
        ("你好肥鲸", "小艺"),
        ("你好肥金", "小艺"),
        ("你好肥京", "小艺"),
        ("美国豆包", "美国豆包"),
        ("你好美国豆包", "美国豆包"),
        ("下面呢", "美国豆包"),
        ("杰米奈", "美国豆包"),
        ("杰米尼", "美国豆包"),
        ("吉米奈", "美国豆包"),
        ("格米奈", "美国豆包"),
        ("加米奈", "美国豆包"),
        ("天命来", "美国豆包"),
        ("你好下面呢", "美国豆包"),
        ("你好杰米奈", "美国豆包"),
        ("你好杰米尼", "美国豆包"),
        ("地铺西克", "小艺"),
        ("迪普西克", "小艺"),
        ("低普瑟克", "小艺"),
        ("你好地铺西克", "小艺"),
    ]
    extra_texts = [item[0] for item in extra_phonetic_keywords]
    extra_encoded = text2token(
        extra_texts,
        tokens=args["tokens"],
        tokens_type=args["tokens_type"],
        bpe_model=args["bpe_model"],
    )

    with open(args["output"], "w", encoding="utf8") as f:
        raw_keywords = args["keywords"]
        for idx, txt in enumerate(encoded_texts):
            orig = raw_keywords[idx] if idx < len(raw_keywords) else "".join(txt)
            clean_tag = orig.replace("▁", "").replace(" ", "_").strip().lower()
            f.write(" ".join(txt) + f" @{clean_tag}\n")

        for idx, txt in enumerate(extra_encoded):
            target_label = extra_phonetic_keywords[idx][1]
            f.write(" ".join(txt) + f" @{target_label}\n")

    logger.debug(f"Keyword file generated: {args['output']}", module="KWS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
