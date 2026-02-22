# 🎬 YouTube AI Video Pipeline v2

**Fully automated AI-powered YouTube video creation — from topic to upload-ready MP4.**

Default LLM: **MiniMax M2 via OpenRouter**. Change any provider, style, or setting by editing one JSON file. No code changes. Ever.

example:
python main.py generate --topic "OpenClaw" --urls "https://openclaw.ai/" "https://github.com/openclaw/openclaw"

---

## How to Run

```bash
# From INSIDE your project folder (AGC_3 or whatever you named it):
cd AGC_3
python main.py generate --topic "Claude 4 just launched"

# Start REST API server:
python main.py serve
```

That is the only way to run it. Always `cd` into the folder first.

---

## How It Works

```
Your Topic
    │
    ▼
┌───────────────┐   ┌─────────────────────┐   ┌─────────────────┐
│ 1. Research   │──▶│ 2. Script           │──▶│ 3. Screenshots  │
│ Web search +  │   │ MiniMax M2 via      │   │ Playwright      │
│ page fetching │   │ OpenRouter writes   │   │ headless Chrome │
└───────────────┘   │ structured script   │   └────────┬────────┘
                    │ with visual markers │            │
                    └─────────────────────┘   ┌────────▼────────┐
                                              │ 4. Narration    │
                                              │ ElevenLabs /    │
                                              │ OpenAI TTS /    │
                                              │ Azure           │
                                              └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │ 5. A/V Sync     │
                                              │ Map visuals to  │
                                              │ audio timeline  │
                                              └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │ 6. FFmpeg       │
                                              │ Assemble MP4    │
                                              │ Ken Burns zoom  │
                                              │ Xfade transitions│
                                              │ Music mix       │
                                              └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │ 7. Metadata     │
                                              │ Title, desc,    │
                                              │ tags, thumbnail │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                         output/your_video.mp4
                                         output/your_video_metadata.json
```

---

## The Only Two Files You Ever Touch

| File | Purpose |
|---|---|
| `.env` | API keys only — your secrets |
| `config/pipeline.json` | Everything else — providers, styles, quality, output |

---

## Quick Start

### 1. Install system dependencies

```bash
# Ubuntu / Debian (RunPod, AWS, etc.)
apt-get install -y ffmpeg fonts-dejavu-core

# macOS
brew install ffmpeg
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

### 3. Set your API keys

```bash
cp .env.example .env
nano .env
```

**Minimum required to run** (default config):
```
OPENROUTER_API_KEY=sk-or-v1-...      ← get at openrouter.ai/keys
GOOGLE_SEARCH_API_KEY=...
GOOGLE_SEARCH_CX=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

### 4. Run

```bash
cd AGC_3
python main.py generate --topic "Claude 4 just launched"
```

---

## Default LLM: MiniMax M2 via OpenRouter

The default in `config/pipeline.json` is:

```json
"llm": {
  "provider": "openrouter",
  "model": {
    "openrouter": "minimax/minimax-m2"
  }
}
```

OpenRouter gives you access to **hundreds of models** through one API key and one `OPENROUTER_API_KEY`. To switch models, just change the model slug in `pipeline.json` — no code changes:

```json
"model": { "openrouter": "minimax/minimax-m2" }
"model": { "openrouter": "anthropic/claude-opus-4" }
"model": { "openrouter": "openai/gpt-4o" }
"model": { "openrouter": "mistralai/mistral-large" }
"model": { "openrouter": "meta-llama/llama-3.1-405b" }
"model": { "openrouter": "google/gemini-pro-1.5" }
```

Full model list: **https://openrouter.ai/models**

---

## Switching Providers — JSON Only, No Code

### LLM

```json
"llm": { "provider": "openrouter" }
```

| Value | Key in .env | Notes |
|---|---|---|
| `openrouter` | `OPENROUTER_API_KEY` | **Default** — access to 100s of models |
| `claude` | `ANTHROPIC_API_KEY` | Direct Anthropic API |
| `openai` | `OPENAI_API_KEY` | Direct OpenAI API |
| `gemini` | `GEMINI_API_KEY` | Direct Google API |

---

### Search

```json
"search": { "provider": "google" }
```

| Value | Key in .env |
|---|---|
| `google` | `GOOGLE_SEARCH_API_KEY` + `GOOGLE_SEARCH_CX` |
| `bing` | `BING_SEARCH_API_KEY` |
| `serpapi` | `SERPAPI_KEY` |
| `searx` | None — free self-hosted |

**Free Searx:**
```bash
docker run -d -p 8080:8080 searxng/searxng
```
Then set `"provider": "searx"` in `pipeline.json`.

---

### Voice

```json
"voice": { "provider": "elevenlabs" }
```

| Value | Key in .env | Notes |
|---|---|---|
| `elevenlabs` | `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` | Best quality, voice cloning |
| `openai_tts` | `OPENAI_API_KEY` | Good quality, cheaper |
| `azure` | `AZURE_TTS_KEY` + `AZURE_TTS_REGION` | Enterprise |

---

### Video Style

```json
"video": { "style": "dark_tech" }
```

| Value | Look |
|---|---|
| `dark_tech` | Dark background, coloured accent bars, Ken Burns zoom |
| `minimal_white` | Clean white, bold text, no zoom |
| `news_room` | Dark grey, red/gold accents |

**Add a custom style** — just add to `video.styles` in `pipeline.json`:
```json
"my_style": {
  "canvas":            { "width": 1920, "height": 1080 },
  "fps":               30,
  "background_colour": "#1A1A2E",
  "accent_colours":    ["#E94560", "#0F3460"],
  "font":              "DejaVuSans-Bold",
  "title_card_layout": "left_accent_bar",
  "ken_burns":         true,
  "ken_burns_zoom":    0.0003
}
```

---

### Script Persona

```json
"script": { "persona": "tech_enthusiast" }
```

| Value | Tone |
|---|---|
| `tech_enthusiast` | Energetic, insightful, conversational |
| `educator` | Calm, clear, step-by-step |
| `hype` | Punchy, excited, short sentences |
| `analyst` | Measured, data-driven, strategic |

---

## Per-Topic Override Files

Run a single video with custom settings without changing the global config.

Create `topics/gpt5_launch.json`:
```json
{
  "topic": "GPT-5 just launched",
  "overrides": {
    "llm.model.openrouter": "openai/gpt-4o",
    "script.persona":        "hype",
    "script.target_minutes": 8,
    "video.style":           "news_room",
    "output.dir":            "./output/gpt5"
  }
}
```

Run it:
```bash
python main.py generate --topic-file topics/gpt5_launch.json
```

---

## CLI Reference

```bash
# Basic
python main.py generate --topic "Your topic here"

# With topic override file
python main.py generate --topic-file topics/my_topic.json

# Override pipeline.json values inline (no file needed)
python main.py generate \
  --topic "Google Gemini Ultra 2" \
  --set llm.model.openrouter=google/gemini-pro-1.5 \
  --set video.style=minimal_white \
  --set script.target_minutes=10

# Start REST API
python main.py serve
```

---

## REST API

```bash
python main.py serve
# Runs at http://localhost:8000
```

**Generate a video:**
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Claude 4 is here",
    "overrides": {
      "llm.model.openrouter": "minimax/minimax-m2",
      "script.persona": "hype",
      "video.style": "dark_tech"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "video_path": "./output/Claude_4_is_here.mp4",
  "metadata_path": "./output/Claude_4_is_here_metadata.json",
  "log": ["1/7 Research…", "2/7 Script…", "...done in 142s"]
}
```

**View active config:**
```bash
curl http://localhost:8000/config
```

---

## Docker

```bash
# Build
docker build -t yt-pipeline .

# CLI
docker run --env-file .env \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/config/pipeline.json:/app/config/pipeline.json \
  yt-pipeline python main.py generate --topic "Latest AI news"

# Server
docker run --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/config/pipeline.json:/app/config/pipeline.json \
  yt-pipeline python main.py serve
```

Mount `pipeline.json` as a volume so you can edit it without rebuilding.

---

## Output Files

**`output/Your_Topic_Title.mp4`** — 1080p video ready to upload to YouTube.

**`output/Your_Topic_Title_metadata.json`:**
```json
{
  "title": "MiniMax M2 Just Changed Everything",
  "description": "Full SEO-optimised description with timestamps...",
  "tags": ["MiniMax", "AI", "OpenRouter", "LLM", ...],
  "category": "Science & Technology",
  "thumbnail_suggestions": [
    "Split screen: MiniMax M2 vs GPT-4o benchmark chart",
    "Bold text: THE MODEL THEY DIDN'T TELL YOU ABOUT",
    "Person at laptop looking shocked at benchmark results"
  ]
}
```

---

## Caching

Results are cached in `./cache/` — re-runs are fast and free:

| What | Cache key |
|---|---|
| Search results | Provider + query hash |
| Page content | URL hash |
| TTS audio | Provider + voice settings + text hash |
| Screenshots | URL hash |

Delete `./cache/` to force fresh fetches.
Delete `./temp/` to force re-processing audio/video.

---

## `pipeline.json` Full Reference

| Key | Default | Options |
|---|---|---|
| `llm.provider` | `openrouter` | `openrouter` `claude` `openai` `gemini` |
| `llm.model.openrouter` | `minimax/minimax-m2` | any slug from openrouter.ai/models |
| `llm.max_tokens` | `8192` | any integer |
| `llm.temperature` | `0.7` | `0.0` – `1.0` |
| `search.provider` | `google` | `google` `bing` `serpapi` `searx` |
| `search.max_results` | `10` | any integer |
| `voice.provider` | `elevenlabs` | `elevenlabs` `openai_tts` `azure` |
| `script.target_minutes` | `12` | any integer |
| `script.persona` | `tech_enthusiast` | `tech_enthusiast` `educator` `hype` `analyst` |
| `video.style` | `dark_tech` | `dark_tech` `minimal_white` `news_room` |
| `video.transitions.type` | `fade` | `fade` `slideleft` `slideright` `wipeleft` `dissolve` |
| `video.background_music.enabled` | `false` | `true` `false` |
| `output.dir` | `./output` | any path |
| `quality_checks.enabled` | `true` | `true` `false` |

---

## Project Structure

```
AGC_3/
├── .env                            ← Your API keys (never commit this)
├── .env.example                    ← Template — copy to .env
├── config/
│   ├── pipeline.json               ← YOUR CONTROL PANEL
│   └── loader.py                   ← reads JSON, builds providers
├── providers/
│   ├── llm/
│   │   ├── base.py                 ← shared interface
│   │   ├── openrouter_provider.py  ← DEFAULT (minimax/minimax-m2)
│   │   ├── claude_provider.py
│   │   ├── openai_provider.py
│   │   └── gemini_provider.py
│   ├── search/
│   │   └── providers.py            ← google, bing, serpapi, searx
│   └── voice/
│       └── providers.py            ← elevenlabs, openai_tts, azure
├── services/                       ← pipeline logic (don't edit)
│   ├── research_service.py
│   ├── script_service.py
│   ├── visual_service.py
│   ├── voice_service.py
│   ├── sync_service.py
│   ├── video_service.py
│   └── metadata_service.py
├── topics/                         ← per-video override files
│   └── example_claude4_launch.json
├── utils/
│   └── models.py
├── main.py                         ← entry point — run this
├── orchestrator.py
├── Dockerfile
└── requirements.txt
```

---

## Adding a New OpenRouter Model (Zero Code)

Just change one line in `pipeline.json`:
```json
"llm": {
  "provider": "openrouter",
  "model": { "openrouter": "mistralai/mistral-large" }
}
```

Browse all available models: **https://openrouter.ai/models**

---

## Troubleshooting

**`ImportError: attempted relative import`**
You're running from the wrong directory. Always:
```bash
cd AGC_3          ← must be INSIDE the folder
python main.py generate --topic "..."
```

**`OPENROUTER_API_KEY is not set`**
Add it to your `.env` file. Get a key at https://openrouter.ai/keys

**OpenRouter 402 error**
Your OpenRouter account has no credits. Add credits at https://openrouter.ai/credits

**OpenRouter model not found**
Check the exact model slug at https://openrouter.ai/models — e.g. `minimax/minimax-m2` not `minimax-m2`

**`playwright install chromium` fails**
```bash
playwright install-deps chromium
playwright install chromium
```

**FFmpeg not found**
```bash
apt-get install -y ffmpeg    # Ubuntu/RunPod
brew install ffmpeg           # macOS
```

**ElevenLabs 401 error**
Check `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` in `.env`.
Voice ID is in your ElevenLabs dashboard under Voices.

**Video too long / too short**
```json
"script": { "target_minutes": 8 }
```

**Sync drift warning**
Raise threshold: `"quality_checks": { "max_sync_drift_sec": 5.0 }`


Here is a high-level breakdown of the codebase and how it works:

1. Main Entry Points

main.py
: The core execution script. You can run it via the CLI to generate a video directly (python main.py generate --topic "...") or launch a REST API server (python main.py serve) to trigger generation via HTTP POST requests.

.env
: Stores sensitive API keys (OpenRouter, Google Search, ElevenLabs, etc.).
config/pipeline.json: The central "control panel". It defines which providers to use (e.g., OpenRouter vs. Anthropic for LLM, ElevenLabs vs. OpenAI for voice), styles, and video settings, meaning you never have to change the Python code to switch tools.
2. The Pipeline (

orchestrator.py
)
The 

PipelineOrchestrator
 manages the end-to-end process in 7 distinct steps, delegating tasks to specific services in the services/ directory:

Research (research_service.py): Searches the web (via Google, Bing, Searx, or direct URLs) and fetches page content to gather facts about the topic.
Scripting (script_service.py): Passes the research to an LLM (default is MiniMax M2 via OpenRouter) to write a structured video script, complete with visual markers for when images should appear on screen.
Visuals (visual_service.py): Uses Playwright (headless Chrome) to capture screenshots or generate relevant visual content based on the script's markers.
Voice/Narration (voice_service.py): Sends the written script text to a Text-to-Speech (TTS) engine (like ElevenLabs or OpenAI) to generate the audio narration.
A/V Sync (sync_service.py): Maps the exact timings of the generated audio to the visual assets to ensure they appear on screen exactly when they are mentioned.
Video Assembly (video_service.py): Uses FFmpeg to stitch everything together into an MP4. This applies transitions (crossfades, wipes), Ken Burns zoom effects, and mixes in background music.
Metadata (metadata_service.py): Generates upload-ready YouTube metadata, including an SEO-optimized title, description, tags, and ideas for the thumbnail.
3. File Outputs & Caching
output/: The final 

.mp4
 video and a _metadata.json file containing the YouTube title/description are saved here in a timestamped folder.
cache/: The system caches expensive API responses (LLM outputs, text-to-speech audio, and search results). If you re-run a pipeline or slightly tweak a setting, it won't waste API credits recreating parts that haven't changed.
In summary, this is a highly modular, config-driven pipeline built to chain together search, LLMs, Text-to-Speech, browser automation, and FFmpeg without requiring code modifications between runs. Let me know if you would like to dive deeper into any specific service or file!
