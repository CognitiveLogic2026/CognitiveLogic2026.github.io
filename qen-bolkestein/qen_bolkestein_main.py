# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import asyncio, sys
from neo4j import GraphDatabase
from qen_multi_agent_router import BatchProcessor
from qen_scoring_engine import get_prompt_fn
from qen_config import QENBolkesteinConfig
from loguru import logger

logger.add("logs/main.log", rotation="500 MB")

class QENOrchestrator:
    def __init__(self):
        _cfg = QENBolkesteinConfig()
        self.driver = GraphDatabase.driver(_cfg.NEO4J_URI, auth=(_cfg.NEO4J_USERNAME, _cfg.NEO4J_PASSWORD))
        self.processor = BatchProcessor(max_workers=10)
    
    def get_businesses(self):
        with self.driver.session() as s:
            r = s.run("MATCH (b:Business) RETURN b")
            return [{"name": b['b'].get("name"), "vertical": b['b'].get("vertical"), "city": b['b'].get("city"), "address": b['b'].get("address"), "phone": b['b'].get("phone"), "website": b['b'].get("website")} for b in r]
    
    def save_score(self, name, sr):
        try:
            with self.driver.session() as s:
                s.run("MATCH (b:Business {name: $name}) SET b.qen_score = $score, b.vs_score = $vs, b.va_score = $va, b.vt_score = $vt, b.confidence = $conf, b.scoring_model = $model, b.qen_status = 'scored', b.scored_at = datetime()", name=name, score=sr.qen_score, vs=sr.vs_score, va=sr.va_score, vt=sr.vt_score, conf=sr.confidence, model=sr.model_used)
            logger.info(f"💾 {name} = {sr.qen_score:.1f}")
            return True
        except Exception as e:
            logger.error(f"❌ {e}")
            return False
    
    async def run(self, batch_size=10):
        logger.info("🚀 QEN Pipeline Started")
        businesses = self.get_businesses()
        logger.info(f"📊 {len(businesses)} businesses loaded")
        successful, failed = 0, 0
        for i in range(0, len(businesses), batch_size):
            batch = businesses[i:i+batch_size]
            vertical = batch[0]["vertical"]
            prompt_fn = get_prompt_fn(vertical)
            results = await self.processor.process_batch(batch, prompt_fn)
            for r in results:
                if self.save_score(r.business_name, r):
                    successful += 1
                else:
                    failed += 1
        logger.info(f"✅ Complete: {successful} OK, {failed} failed")
        return successful, failed
    
    def close(self):
        self.driver.close()

async def main():
    orch = QENOrchestrator()
    try:
        await orch.run(batch_size=7)
    finally:
        orch.close()

if __name__ == "__main__":
    asyncio.run(main())
