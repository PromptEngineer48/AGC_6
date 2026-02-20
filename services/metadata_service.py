"""Metadata Service (v2)"""
from __future__ import annotations
import sys as _sys
import os as _os
# Add the project root (this file's parent or grandparent) to sys.path
_this_file = _os.path.abspath(__file__)
_project_root = _os.path.dirname(_os.path.dirname(_this_file))  # goes up to AGC_4/
if _project_root not in _sys.path:
    _sys.path.insert(0, _project_root)
# Also add project root itself (for files directly in AGC_4/)
_self_dir = _os.path.dirname(_this_file)
if _self_dir not in _sys.path:
    _sys.path.insert(0, _self_dir)

import json, logging, re
from config.loader import RuntimeConfig
from utils.models import ResearchResult, VideoMetadata, VideoScript

logger = logging.getLogger(__name__)

class MetadataService:
    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg

    async def generate(self, script: VideoScript, research: ResearchResult) -> VideoMetadata:
        logger.info("[Metadata] Generating")
        meta_cfg = self.cfg._raw.get("metadata", {})
        resp = await self.cfg.llm.complete(
            user_prompt=(
                f"YouTube SEO expert. Generate metadata for a tech video.\n\n"
                f"TITLE: {script.title}\nTOPIC: {script.topic}\n"
                f"KEY FACTS:\n" + "\n".join(f"• {f}" for f in research.key_facts[:8]) +
                f"\n\nReturn JSON: {{ \"title\": \"...(max {meta_cfg.get('title_max_chars', 100)} chars)\", "
                f"\"description\": \"...(300-500 words)\", \"tags\": [...{meta_cfg.get('max_tags', 20)} tags], "
                "\"thumbnail_suggestions\": [\"...\", \"...\", \"...\"] }}\nReturn ONLY valid JSON."
            ),
            max_tokens=2048,
        )
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", resp.text.strip())
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"title": script.title, "description": f"Video about {script.topic}", "tags": [], "thumbnail_suggestions": []}
        tags = list(set(data.get("tags", []) + meta_cfg.get("default_tags", [])))[:meta_cfg.get("max_tags", 20)]
        return VideoMetadata(
            title=data.get("title", script.title),
            description=data.get("description", ""),
            tags=tags,
            thumbnail_suggestions=data.get("thumbnail_suggestions", []),
            category=meta_cfg.get("category", "Science & Technology"),
        )
