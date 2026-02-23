"""
Voice Providers
────────────────
Unified interface for TTS backends.
Switch via pipeline.json: voice.provider = "elevenlabs" | "openai_tts" | "azure"
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
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path

import aiohttp

logger = logging.getLogger(__name__)


class BaseVoiceProvider(ABC):
    @abstractmethod
    async def synthesise(
        self,
        text: str,
        output_path: Path,
        voice_settings: dict,
    ) -> None:
        """Synthesise text to audio file at output_path."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @staticmethod
    async def get_duration(path: Path) -> float:
        """FFprobe-based duration detection, shared by all providers."""
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        try:
            return float(stdout.decode().strip())
        except ValueError:
            return 0.0


# ── ElevenLabs ────────────────────────────────────────────────────────────────

class ElevenLabsProvider(BaseVoiceProvider):
    BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.environ["ELEVENLABS_API_KEY"]
        self.voice_id = os.environ["ELEVENLABS_VOICE_ID"]

    @property
    def provider_name(self) -> str:
        return "elevenlabs"

    async def synthesise(
        self, text: str, output_path: Path, voice_settings: dict
    ) -> None:
        url = self.BASE_URL.format(voice_id=self.voice_id)
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability":         voice_settings.get("stability", 0.5),
                "similarity_boost":  voice_settings.get("similarity_boost", 0.75),
                "style":             voice_settings.get("style", 0.0),
                "use_speaker_boost": voice_settings.get("use_speaker_boost", True),
            },
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(f"ElevenLabs {resp.status}: {body}")
                output_path.write_bytes(await resp.read())


# ── OpenAI TTS ────────────────────────────────────────────────────────────────

class OpenAITTSProvider(BaseVoiceProvider):
    def __init__(self, model: str):
        self.model = model
        try:
            from openai import AsyncOpenAI
            api_key = os.getenv("OPENAI_TTS_API_KEY") or os.environ["OPENAI_API_KEY"]
            self._client = AsyncOpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package required: pip install openai")

    @property
    def provider_name(self) -> str:
        return "openai_tts"

    async def synthesise(
        self, text: str, output_path: Path, voice_settings: dict
    ) -> None:
        voice_name = voice_settings.get("voice_name", "onyx")
        speed = voice_settings.get("speed", 1.0)

        response = await self._client.audio.speech.create(
            model=self.model,
            voice=voice_name,
            input=text,
            speed=speed,
            response_format="mp3",
        )
        output_path.write_bytes(response.content)


# ── Azure Cognitive Services TTS ──────────────────────────────────────────────

class AzureTTSProvider(BaseVoiceProvider):
    SSML_TEMPLATE = """<speak version='1.0' xml:lang='en-US'>
  <voice name='{voice_name}'>
    <prosody rate='{rate}' pitch='{pitch}'>{text}</prosody>
  </voice>
</speak>"""

    def __init__(self, model: str):
        self.model = model  # unused for Azure but kept for interface consistency
        self.api_key = os.environ["AZURE_TTS_KEY"]
        self.region = os.getenv("AZURE_TTS_REGION", "eastus")
        self.endpoint = (
            f"https://{self.region}.tts.speech.microsoft.com"
            "/cognitiveservices/v1"
        )

    @property
    def provider_name(self) -> str:
        return "azure"

    async def synthesise(
        self, text: str, output_path: Path, voice_settings: dict
    ) -> None:
        voice_name = voice_settings.get("voice_name", "en-US-GuyNeural")
        rate = voice_settings.get("rate", "+0%")
        pitch = voice_settings.get("pitch", "+0Hz")

        ssml = self.SSML_TEMPLATE.format(
            voice_name=voice_name, rate=rate, pitch=pitch, text=text
        )
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.endpoint, data=ssml.encode(), headers=headers
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(f"Azure TTS {resp.status}: {body}")
                output_path.write_bytes(await resp.read())


# ── RunPod Gradio TTS ────────────────────────────────────────────────────────
class RunPodProvider(BaseVoiceProvider):
    def __init__(self, model: str):
        self.model = model
        try:
            from gradio_client import Client
        except ImportError:
            raise ImportError("gradio_client package required: pip install gradio_client")
            
        self.api_url = "https://qughf6g12na7uk-8002.proxy.runpod.net/"
        # We initialize the client once to reuse the connection.
        # Giving it a 5-minute timeout because RunPod emulation can sometimes be slow.
        self.client = Client(self.api_url, httpx_kwargs={"timeout": 300.0})

    @property
    def provider_name(self) -> str:
        return "runpod"

    async def synthesise(
        self, text: str, output_path: Path, voice_settings: dict
    ) -> None:
        from gradio_client import handle_file
        import shutil
        
        # Read reference file path from settings or fallback to default
        default_ref = str((Path(__file__).parent / "my_voice" / "ref.wav").absolute())
        ref_wav_path = voice_settings.get("ref_wav_path", default_ref)
        
        # If the path from settings is relative, resolve it relative to the current working directory
        if not Path(ref_wav_path).is_absolute():
            ref_wav_path = str(Path(ref_wav_path).absolute())
        
        if not Path(ref_wav_path).exists():
             logger.warning(f"RunPod TTS: Reference wav not found at {ref_wav_path}")
        
        # Gradio client predict is blocking, so we run it in a thread pool to avoid 
        # blocking the async event loop, especially since this is an external network call.
        def _run_gradio():
            return self.client.predict(
                emo_control_method="Same as the voice reference",
                prompt=handle_file(ref_wav_path),
                text=text,
                emo_ref_path=handle_file(ref_wav_path),
                emo_weight=0.65,
                vec1=0, vec2=0, vec3=0, vec4=0,
                vec5=0, vec6=0, vec7=0, vec8=0,
                emo_text="",
                emo_random=False,
                max_text_tokens_per_segment=120,
                param_16=True,
                param_17=0.8,
                param_18=30,
                param_19=0.8,
                param_20=0,
                param_21=3,
                param_22=10,
                param_23=1500,
                api_name="/gen_single"
            )
            
        # Run blocking gradio logic
        result = await asyncio.to_thread(_run_gradio)

        # Parse output
        if isinstance(result, dict):
            temp_file = result.get("value")
        else:
            temp_file = result
            
        if not temp_file or not Path(temp_file).exists():
            raise RuntimeError(f"RunPod TTS failed, unexpected result format: {result}")

        # Copy gradio temp file to the expected output_path cache location
        shutil.copyfile(temp_file, output_path)

# ── Registry ──────────────────────────────────────────────────────────────────

_VOICE_PROVIDERS: dict[str, type[BaseVoiceProvider]] = {
    "elevenlabs": ElevenLabsProvider,
    "openai_tts": OpenAITTSProvider,
    "azure":      AzureTTSProvider,
    "runpod":     RunPodProvider,
}


def get_voice_provider(name: str, model: str) -> BaseVoiceProvider:
    cls = _VOICE_PROVIDERS.get(name.lower())
    if not cls:
        raise ValueError(
            f"Unknown voice provider '{name}'. "
            f"Available: {list(_VOICE_PROVIDERS)}"
        )
    return cls(model)
