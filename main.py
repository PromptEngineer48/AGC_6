#!/usr/bin/env python3
"""
YouTube AI Video Pipeline v2 — Entry Point

Works BOTH ways:
  # From INSIDE the folder (recommended):
  cd AGC_4
  python main.py generate --topic "Claude Opus 4.6 just launched"

  # From OUTSIDE the folder:
  python -m AGC_4.main generate --topic "Claude Opus 4.6 just launched"
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# ── Fix imports for BOTH run modes ───────────────────────────────────────────
# _HERE = the folder containing this file (e.g. /root/AGC_4)
# We always add _HERE to sys.path so that:
#   "import orchestrator"      works (finds AGC_4/orchestrator.py)
#   "import config.loader"     works (finds AGC_4/config/loader.py)
#   "import providers.llm..."  works (finds AGC_4/providers/...)
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# ── Also add PARENT so python -m AGC_4.main works ────────────────────────────
_PARENT = _HERE.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

# ── Now safe to import project modules ───────────────────────────────────────
try:
    from dotenv import load_dotenv
    _env_path = _HERE / ".env"
    print(f"DEBUG: Loading .env from {_env_path}")
    load_dotenv(dotenv_path=_env_path)
    load_dotenv()  # also check cwd
except ImportError:
    print("WARNING: python-dotenv not installed. .env file will be ignored.")
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = _HERE / "config" / "pipeline.json"


def _get_loader():
    from config.loader import ConfigLoader
    return ConfigLoader(CONFIG_PATH)


def _get_orchestrator(cfg):
    from orchestrator import PipelineOrchestrator
    return PipelineOrchestrator(cfg)


def _set_nested(d, dot_key, value):
    from config.loader import _set_nested as _sn
    _sn(d, dot_key, value)


def _apply_set_overrides(set_args):
    if not set_args:
        return None
    overrides = {}
    for item in set_args:
        if "=" not in item:
            raise ValueError(f"--set must be key=value, got: {item}")
        k, v = item.split("=", 1)
        if v.lower() == "true":    v = True
        elif v.lower() == "false": v = False
        elif v.replace(".", "").isdigit():
            v = float(v) if "." in v else int(v)
        overrides[k] = v
    return overrides


async def run_generate(args) -> int:
    loader = _get_loader()
    topic_file = Path(args.topic_file) if getattr(args, "topic_file", None) else None
    cfg = loader.load(topic_file)

    set_overrides = _apply_set_overrides(getattr(args, "set", []) or [])
    if set_overrides:
        raw = json.loads(CONFIG_PATH.read_text())
        for k, v in set_overrides.items():
            _set_nested(raw, k, v)
        cfg = loader._build(raw)

    urls = getattr(args, "urls", None)
    if urls:
        # Force provider to direct and set the query to the joined URLs
        cfg._raw["search"]["provider"] = "direct"
        cfg._raw["search"]["urls"] = urls
        # REBUILD the runtime config so 'search' becomes DirectUrlProvider
        cfg = loader._build(cfg._raw)

    topic = getattr(args, "topic", "") or ""
    if not topic and topic_file:
        doc = json.loads(topic_file.read_text())
        topic = doc.get("topic", "")
    if not topic:
        print("ERROR: Provide --topic or --topic-file with a topic field")
        return 1

    for d in [cfg.output_dir, cfg.cache_dir, cfg.temp_dir]:
        Path(d).mkdir(parents=True, exist_ok=True)

    result = await _get_orchestrator(cfg).run(topic)

    if result.success:
        print(f"\n✅ Success!")
        print(f"   Video    : {result.video_path}")
        print(f"   Metadata : {result.metadata_json_path}")
        if result.metadata:
            print(f"   Title    : {result.metadata.title}")
        return 0
    else:
        print(f"\n❌ Failed: {result.error_message}")
        return 1


async def run_server(args) -> None:
    try:
        from aiohttp import web
    except ImportError:
        print("ERROR: pip install aiohttp")
        sys.exit(1)

    loader = _get_loader()

    async def handle_generate(req):
        try:
            body = await req.json()
            topic = body.get("topic", "").strip()
            if not topic:
                return web.json_response({"error": "topic required"}, status=400)
            overrides = body.get("overrides", {})
            cfg = loader.load()
            if overrides:
                raw = json.loads(CONFIG_PATH.read_text())
                for k, v in overrides.items():
                    _set_nested(raw, k, v)
                cfg = loader._build(raw)
            for d in [cfg.output_dir, cfg.cache_dir, cfg.temp_dir]:
                Path(d).mkdir(parents=True, exist_ok=True)
            result = await _get_orchestrator(cfg).run(topic)
            return web.json_response({
                "success": result.success,
                "video_path": str(result.video_path) if result.video_path else None,
                "metadata_path": str(result.metadata_json_path) if result.metadata_json_path else None,
                "error": result.error_message,
                "log": result.pipeline_log,
            })
        except Exception as exc:
            logger.exception(exc)
            return web.json_response({"error": str(exc)}, status=500)

    app = web.Application()
    app.router.add_get("/health", lambda _: web.json_response({"status": "ok"}))
    app.router.add_get("/config", lambda _: web.json_response(json.loads(CONFIG_PATH.read_text())))
    app.router.add_post("/generate", handle_generate)

    port = int(os.getenv("PORT", "8000"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    logger.info(f"Server on http://0.0.0.0:{port}")
    await asyncio.Event().wait()


def main():
    p = argparse.ArgumentParser(description="YouTube AI Video Pipeline v2")
    sub = p.add_subparsers(dest="cmd")

    gen = sub.add_parser("generate", help="Generate a video")
    gen.add_argument("--topic", default="", help="Video topic")
    gen.add_argument("--topic-file", default=None, help="Path to topic override JSON")
    gen.add_argument("--set", nargs="*", metavar="key=value",
                     help="Override pipeline.json values inline")
    gen.add_argument("--urls", nargs="+", help="Direct URLs to use for research (skips search)")

    sub.add_parser("serve", help="Start REST API server")

    args = p.parse_args()

    if args.cmd == "generate":
        sys.exit(asyncio.run(run_generate(args)))
    elif args.cmd == "serve":
        asyncio.run(run_server(args))
    else:
        p.print_help()


if __name__ == "__main__":
    main()
