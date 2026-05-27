# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import asyncio, json, os
from dataclasses import dataclass
from anthropic import Anthropic
import aiohttp
from loguru import logger

logger.add("logs/router.log", rotation="500 MB")

@dataclass
class ScoreResult:
    business_name: str
    vertical: str
    vs_score: float
    va_score: float
    vt_score: float
    qen_score: float
    confidence: float
    model_used: str

class LLMRouter:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.ollama_url = "http://localhost:11434"
    
    def select_model(self, vertical):
        m = {"ristorazione": "claude-sonnet-4-20250514", "alberghiero": "claude-sonnet-4-20250514", "balneare": "mistral:7b"}
        return m.get(vertical.lower(), "claude-sonnet-4-20250514")
    
    async def call_claude(self, prompt, name):
        try:
            r = self.anthropic.messages.create(model="claude-sonnet-4-20250514", max_tokens=1000, messages=[{"role": "user", "content": prompt}])
            t = r.content[0].text
            s = t.find('{')
            e = t.rfind('}') + 1
            result = json.loads(t[s:e])
            logger.info(f"✅ Claude: {name} = {result.get('qen_score', 0):.1f}")
            return result, result.get("confidence", 0.8)
        except Exception as e:
            logger.error(f"❌ Claude: {e}")
            return {"vs_score": 50, "va_score": 50, "vt_score": 50, "qen_score": 50, "confidence": 0.3}, 0.3
    
    async def call_ollama(self, prompt, name):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.ollama_url}/api/generate", json={"model": "mistral:7b", "prompt": prompt, "stream": False}, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    d = await resp.json()
                    t = d.get("response", "")
                    s = t.find('{')
                    e = t.rfind('}') + 1
                    result = json.loads(t[s:e])
                    logger.info(f"✅ Ollama: {name} = {result.get('qen_score', 0):.1f}")
                    return result, result.get("confidence", 0.65)
        except Exception as e:
            logger.error(f"❌ Ollama: {e}")
            return {"vs_score": 50, "va_score": 50, "vt_score": 50, "qen_score": 50, "confidence": 0.3}, 0.3
    
    async def route_and_score(self, business, prompt_fn):
        name = business["name"]
        vertical = business["vertical"]
        model = self.select_model(vertical)
        logger.info(f"🔀 Routing {name} ({vertical}) → {model}")
        prompt = prompt_fn(business)
        if "claude" in model:
            result, conf = await self.call_claude(prompt, name)
        else:
            result, conf = await self.call_ollama(prompt, name)
        return ScoreResult(business_name=name, vertical=vertical, vs_score=result.get("vs_score", 50), va_score=result.get("va_score", 50), vt_score=result.get("vt_score", 50), qen_score=result.get("qen_score", 50), confidence=conf, model_used=model)

class BatchProcessor:
    def __init__(self, max_workers=10):
        self.router = LLMRouter()
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def process_batch(self, businesses, prompt_fn):
        tasks = [self._process(b, prompt_fn) for b in businesses]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    async def _process(self, business, prompt_fn):
        async with self.semaphore:
            return await self.router.route_and_score(business, prompt_fn)
