"""
Research Service (v2 — config-driven)
Uses cfg.llm for query generation and fact extraction.
Uses cfg.search for web search.
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

import asyncio
import hashlib
import json
import logging
import re
from pathlib import Path

import aiohttp
import trafilatura

from config.loader import RuntimeConfig
from utils.models import ResearchFinding, ResearchResult

logger = logging.getLogger(__name__)


class ResearchService:
    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg
        self.cache_dir = Path(cfg.cache_dir) / "research"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def research(self, topic: str) -> ResearchResult:
        logger.info(f"[Research] Topic: {topic}")
        
        # Initial search
        queries = await self._generate_queries(topic)
        all_findings = await self._run_search_round(queries)
        
        # Deep Research Loop
        deep_research = self.cfg._raw.get("search", {}).get("deep_research", False)
        depth = self.cfg._raw.get("search", {}).get("depth", 1)
        
        if deep_research and depth > 1:
            for i in range(depth - 1):
                logger.info(f"[Research] Deep Research Round {i+2}/{depth}...")
                new_queries = await self._analyze_and_generate_followup_queries(topic, all_findings, i + 2)
                if not new_queries:
                    break
                new_findings = await self._run_search_round(new_queries)
                all_findings.extend(new_findings)
        
        # Deduplicate and sort
        seen: set[str] = set()
        unique = []
        for f in all_findings:
            if f.url not in seen:
                seen.add(f.url)
                unique.append(f)
        
        # Sort by relevance and fetch content
        top_n = self.cfg._raw["search"]["top_pages_to_fetch"] * (depth if deep_research else 1)
        top = sorted(unique, key=lambda x: x.relevance_score, reverse=True)[:top_n]
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
        ) as session:
            await asyncio.gather(*[self._fetch_content(session, f) for f in top], return_exceptions=True)

        return await self._extract_facts(topic, [f for f in top if f.full_content])

    async def _run_search_round(self, queries: list[str]) -> list[ResearchFinding]:
        findings: list[ResearchFinding] = []
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
        ) as session:
            results = await asyncio.gather(
                *[self._search_cached(session, q) for q in queries],
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, Exception):
                    logger.error(f"[Research] Search error: {r}")
                else:
                    findings.extend(r)
        return findings

    async def _generate_queries(self, topic: str) -> list[str]:
        # If we have direct URLs, we don't need to generate queries.
        # We just return one "query" that is our list of URLs, 
        # which DirectUrlProvider.search expects.
        if self.cfg._raw.get("search", {}).get("urls"):
            return [",".join(self.cfg._raw["search"]["urls"])]

        resp = await self.cfg.llm.complete(
            user_prompt=(
                f"Generate 4 targeted search queries to research this topic for a YouTube "
                f"tech video: '{topic}'\n\nReturn ONLY a JSON array of strings."
            ),
            max_tokens=512,
        )
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", resp.text.strip())
        try:
            queries = json.loads(raw)
            return queries[:4] if isinstance(queries, list) else [topic]
        except json.JSONDecodeError:
            return [topic, f"{topic} announcement", f"{topic} review"]

    async def _search_cached(self, session, query: str) -> list[ResearchFinding]:
        cache_key = hashlib.md5(f"{self.cfg.search.provider_name}:{query}".encode()).hexdigest()
        cache_path = self.cache_dir / f"search_{cache_key}.json"
        if cache_path.exists():
            return [ResearchFinding(**f) for f in json.loads(cache_path.read_text())]
        raw_results = await self.cfg.search.search(session, query, self.cfg._raw["search"]["max_results"])
        findings = [
            ResearchFinding(title=r.title, url=r.url, snippet=r.snippet, relevance_score=1.0 - r.position * 0.1)
            for r in raw_results
        ]
        cache_path.write_text(json.dumps([f.__dict__ for f in findings], default=str))
        return findings

    async def _fetch_content(self, session, finding: ResearchFinding) -> None:
        cache_key = hashlib.md5(finding.url.encode()).hexdigest()
        cache_path = self.cache_dir / f"page_traf_{cache_key}.txt"
        
        if cache_path.exists():
            finding.full_content = cache_path.read_text()
            return

    async def _fetch_content(self, session, finding: ResearchFinding) -> None:
        cache_key = hashlib.md5(finding.url.encode()).hexdigest()
        cache_path = self.cache_dir / f"page_traf_{cache_key}.txt"
        
        if cache_path.exists():
            finding.full_content = cache_path.read_text()
            return

        try:
            # Use aiohttp for non-blocking fetch
            headers = {"Accept-Encoding": "gzip, deflate", "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}
            async with session.get(finding.url, allow_redirects=True, headers=headers) as resp:
                if resp.status != 200:
                    return
                # Detect encoding or use default
                html = await resp.text(errors="replace")

            # Use trafilatura for extraction (CPU bound, but fast enough to keep in loop for now)
            # Ideally run in executor, but this is better than blocking network I/O
            text = trafilatura.extract(html, include_comments=False, include_tables=False)
            
            if not text:
                 # Fallback to simple regex if trafilatura fails
                text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL)
                text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
            
            if text:
                finding.full_content = text[:12000]
                cache_path.write_text(finding.full_content)
                
        except Exception as exc:
            logger.warning(f"[Research] Fetch failed {finding.url}: {exc}")

    async def _analyze_and_generate_followup_queries(self, topic: str, current_findings: list[ResearchFinding], round_num: int) -> list[str]:
        # Summarize what we have to find gaps
        snippets = "\n".join([f"- {f.title}: {f.snippet}" for f in current_findings[:10]])
        
        prompt = (
            f"Researching '{topic}'. Round {round_num-1} findings:\n{snippets}\n\n"
            "Identify 3 missing perspectives or specific details needed for a comprehensive YouTube video.\n"
            "Generate 3 new, TARGETED search queries to fill these gaps.\n"
            "Return ONLY a JSON array of strings array."
        )
        
        resp = await self.cfg.llm.complete(user_prompt=prompt, max_tokens=256)
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", resp.text.strip())
        try:
            queries = json.loads(raw)
            return queries if isinstance(queries, list) else []
        except:
            return []

    async def _extract_facts(self, topic: str, findings: list[ResearchFinding]) -> ResearchResult:
        snippets = "\n\n".join(
            f"SOURCE: {f.title}\nURL: {f.url}\n{(f.full_content or f.snippet)[:1500]}\n---"
            for f in findings[:8]
        )
        resp = await self.cfg.llm.complete(
            user_prompt=(
                f"Researching '{topic}' for a YouTube tech video.\n\nSources:\n{snippets}\n\n"
                'Return JSON: { "key_facts": [...], "structured_summary": "...", "query_used": "..." }\n'
                "8-15 specific key_facts. Return ONLY valid JSON."
            ),
            max_tokens=2048,
        )
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", resp.text.strip())
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"key_facts": [f.snippet for f in findings[:8]], "structured_summary": f"Research on: {topic}", "query_used": topic}
        return ResearchResult(
            topic=topic, query_used=data.get("query_used", topic), findings=findings,
            key_facts=data.get("key_facts", []), structured_summary=data.get("structured_summary", ""),
            relevant_urls=[f.url for f in findings if f.full_content],
        )
