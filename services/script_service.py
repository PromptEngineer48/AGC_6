"""
Script Generation Service (v2 — config-driven)
Persona, tone and section structure all come from pipeline.json.
"""
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

import json
import logging
import re

from config.loader import RuntimeConfig
from utils.models import ResearchResult, ScriptSection, VideoScript, VisualMarker

logger = logging.getLogger(__name__)

_SYSTEM = """You are an expert YouTube scriptwriter specialising in tech content.
Write in a {tone} style for {audience}.
{style}. {opener_hook}.
Embed visual cues using [SCREENSHOT: https://url | search_query] and [VISUAL: description] markers.
The 'search_query' should be 3-5 words of exact text found on that webpage (e.g. a table heading, key benchmark, or quote) that perfectly matches the audio narration.
We will use this to automatically scroll to the exact part of the page.
You MUST include at least one visual marker every 8-10 seconds of audio.
CRITICAL: Whenever you read off a benchmark result, pricing figure, or specific comparison fact, you MUST immediately insert a [SCREENSHOT: url | exact_table_header] marker corresponding to it.
Target word count: {target_words} words (~{target_minutes} minutes at 150 wpm).
Return ONLY valid JSON, no markdown fences."""

_USER = """Create a YouTube script about: {topic}

RESEARCH SUMMARY:
{summary}

KEY FACTS:
{facts}

RELEVANT URLS TO SCREENSHOT:
{urls}

Return JSON:
{{
  "title": "engaging video title",
  "sections": [
    {{
      "section_id": "intro",
      "section_type": "intro",
      "title": "Section Title",
      "narration_text": "Full narration with [SCREENSHOT: url | exact text to find] markers"
    }}
  ]
}}

Include {min_sections}-{max_sections} sections. Types: {section_types}."""


class ScriptService:
    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg

    async def generate_script(self, research: ResearchResult) -> VideoScript:
        logger.info(f"[Script] Generating for: {research.topic}")
        persona = self.cfg.persona
        target_words = self.cfg.target_minutes * self.cfg.words_per_minute
        raw_cfg = self.cfg._raw

        system = _SYSTEM.format(
            tone=persona["tone"],
            audience=persona["audience"],
            style=persona["style"],
            opener_hook=persona["opener_hook"],
            target_words=target_words,
            target_minutes=self.cfg.target_minutes,
        )
        sections_cfg = raw_cfg["script"]["sections"]
        user = _USER.format(
            topic=research.topic,
            summary=research.structured_summary,
            facts="\n".join(f"• {f}" for f in research.key_facts),
            urls="\n".join(research.relevant_urls[:10]),
            min_sections=sections_cfg["min"],
            max_sections=sections_cfg["max"],
            section_types=", ".join(sections_cfg["allowed_types"]),
        )

        resp = await self.cfg.llm.complete(
            user_prompt=user, system_prompt=system, max_tokens=8192
        )
        
        # Robustly extract JSON from the LLM response
        text = resp.text.strip()
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            raw = match.group(1)
        else:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                raw = text[start:end+1]
            else:
                raw = text
                
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"[Script] Failed to parse JSON. Raw LLM output:\n{text}")
            raise e
        script = self._parse(research.topic, data)
        logger.info(f"[Script] '{script.title}' — {len(script.sections)} sections, ~{script.total_estimated_seconds/60:.1f}min")
        return script

    def _parse(self, topic: str, data: dict) -> VideoScript:
        sections: list[ScriptSection] = []
        t = 0.0
        for raw in data.get("sections", []):
            narration = raw.get("narration_text", "")
            markers, clean = _extract_markers(narration, raw["section_id"])
            dur = (len(clean.split()) / self.cfg.words_per_minute) * 60
            sections.append(ScriptSection(
                section_id=raw.get("section_id", f"s{len(sections)}"),
                section_type=raw.get("section_type", "main"),
                title=raw.get("title", ""),
                narration_text=clean,
                visual_markers=markers,
                estimated_duration_seconds=dur,
                start_time=t,
            ))
            t += dur
        return VideoScript(
            topic=topic, title=data.get("title", topic),
            sections=sections,
            full_text="\n\n".join(s.narration_text for s in sections),
            total_estimated_seconds=t,
        )


def _extract_markers(narration: str, section_id: str) -> tuple[list[VisualMarker], str]:
    markers = []
    # Match both [SCREENSHOT: url] and [SCREENSHOT: url | focus_text]
    for match in re.finditer(r"\[SCREENSHOT:\s*(https?://[^\]|]+)(?:\s*\|\s*([^\]]+))?\]", narration):
        url = match.group(1).strip()
        focus_text = match.group(2).strip() if match.group(2) else None
        markers.append(VisualMarker(marker_type="screenshot", url=url, focus_text=focus_text, section_id=section_id))
    for desc in re.findall(r"\[VISUAL:\s*([^\]]+)\]", narration):
        markers.append(VisualMarker(marker_type="visual", description=desc.strip(), section_id=section_id))
    clean = re.sub(r"\[(?:SCREENSHOT|VISUAL):[^\]]*\]", "", narration)
    return markers, re.sub(r"\s+", " ", clean).strip()
