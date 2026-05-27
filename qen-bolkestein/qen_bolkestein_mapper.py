# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import asyncio, json, logging, os, sys
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from neo4j import GraphDatabase
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qen_config import QENBolkesteinConfig
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
@dataclass
class BusinessEntity:
    name: str
    vertical: str
    region: str
    address: str
    city: str
    province: str
    phone: Optional[str] = None
    website: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = "cna"
    discovered_at: str = None
    confidence: float = 0.0
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now().isoformat()
    def to_dict(self):
        return asdict(self)
class Neo4jManager:
    def __init__(self, config):
        self.uri = config.NEO4J_URI
        self.username = config.NEO4J_USERNAME
        self.password = 'qen_password_2026'
        self.driver = None
    def connect(self) -> bool:
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            with self.driver.session() as session:
                session.run("RETURN 1").consume()
            logger.info(f"✅ Neo4j: {self.uri}")
            return True
        except Exception as e:
            logger.error(f"❌ {e}")
            return False
    def disconnect(self):
        if self.driver:
            self.driver.close()
    def create_business_node(self, b: BusinessEntity) -> bool:
        try:
            query = "CREATE (b:Business {name: $name, vertical: $vertical, region: $region, address: $address, city: $city, province: $province, phone: $phone, website: $website, latitude: $latitude, longitude: $longitude, source: $source, discovered_at: $discovered_at, confidence: $confidence, qen_score: 0.0, qen_status: 'pending'}) RETURN b"
            with self.driver.session() as session:
                session.run(query, **b.to_dict())
            return True
        except Exception as e:
            logger.warning(f"Error {b.name}: {e}")
            return False
    def business_exists(self, name: str, city: str) -> bool:
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (b:Business {name: $name, city: $city}) RETURN COUNT(b) as c", name=name, city=city)
                return result.single()["c"] > 0
        except:
            return False
    def get_stats(self) -> Dict:
        try:
            with self.driver.session() as session:
                r = session.run("MATCH (b:Business) RETURN COUNT(b) as t, COUNT(CASE WHEN b.vertical='ristorazione' THEN 1 END) as r, COUNT(CASE WHEN b.vertical='alberghiero' THEN 1 END) as a, COUNT(CASE WHEN b.vertical='balneare' THEN 1 END) as ba")
                row = r.single()
                return {"total": row["t"], "ristorazione": row["r"], "alberghiero": row["a"], "balneare": row["ba"]}
        except:
            return {}
class CNAScraper:
    async def scrape_cna_bologna_restaurants(self) -> List[BusinessEntity]:
        logger.info("📍 Scraping CNA Bologna (MOCK)...")
        return [
            BusinessEntity(name="Le Sfogline", vertical="ristorazione", region="bologna", address="Via Bologna 123", city="Bologna", province="BO", phone="051123456", confidence=0.95),
            BusinessEntity(name="Bottega Contadina", vertical="ristorazione", region="bologna", address="Via Bologna 456", city="Bologna", province="BO", confidence=0.92),
            BusinessEntity(name="Trattoria Bertozzi", vertical="ristorazione", region="bologna", address="Via Bologna 789", city="Bologna", province="BO", confidence=0.88),
        ]
    async def scrape_cna_bologna_hotels(self) -> List[BusinessEntity]:
        logger.info("📍 Scraping Hotels (MOCK)...")
        return [
            BusinessEntity(name="Hotel Bologna", vertical="alberghiero", region="bologna", address="Via Hotel 100", city="Bologna", province="BO", confidence=0.91),
            BusinessEntity(name="Ahimè", vertical="alberghiero", region="bologna", address="Via Hotel 200", city="Bologna", province="BO", confidence=0.87),
        ]
    async def scrape_cna_rimini_beaches(self) -> List[BusinessEntity]:
        logger.info("📍 Scraping Beaches (MOCK)...")
        return [
            BusinessEntity(name="Stabilimento Spiaggia", vertical="balneare", region="riviera_romagnola", address="Lungomare 1", city="Rimini", province="RN", confidence=0.89),
            BusinessEntity(name="Beach Club Marina", vertical="balneare", region="riviera_romagnola", address="Lungomare 50", city="Rimini", province="RN", confidence=0.85),
        ]
class QENBolkesteinMapper:
    def __init__(self, config):
        self.config = config
        self.neo4j = Neo4jManager(config)
        self.scraper = CNAScraper()
        self.businesses = []
    async def run_full_discovery(self) -> Dict:
        logger.info("\n" + "="*80)
        logger.info("QEN BOLKESTEIN 2027 - DISCOVERY PIPELINE")
        logger.info("="*80 + "\n")
        if not self.neo4j.connect():
            return {"status": "error"}
        try:
            r = await self.scraper.scrape_cna_bologna_restaurants()
            h = await self.scraper.scrape_cna_bologna_hotels()
            b = await self.scraper.scrape_cna_rimini_beaches()
            self.businesses = r + h + b
            logger.info(f"✅ Scraped: {len(self.businesses)}\n")
            created = 0
            for bus in self.businesses:
                if not self.neo4j.business_exists(bus.name, bus.city):
                    if self.neo4j.create_business_node(bus):
                        created += 1
            stats = self.neo4j.get_stats()
            logger.info("STATS:")
            for k, v in stats.items():
                logger.info(f"  {k}: {v}")
            logger.info("\n" + "="*80)
            logger.info("✅ PIPELINE COMPLETED")
            logger.info("="*80 + "\n")
            return {"status": "success", "created": created, "stats": stats}
        finally:
            self.neo4j.disconnect()
async def main():
    QENBolkesteinConfig.load_from_env_file()
    QENBolkesteinConfig.validate()
    mapper = QENBolkesteinMapper(QENBolkesteinConfig)
    result = await mapper.run_full_discovery()
    logger.info(f"Result: {json.dumps(result, indent=2)}")
    return 0 if result.get("status") == "success" else 1
if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
