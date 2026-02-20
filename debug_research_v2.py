
import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.loader import ConfigLoader
from services.research_service import ResearchService
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("--- Starting Deep Research Verification ---")
    
    # Load config
    config_path = Path("config/pipeline.json")
    loader = ConfigLoader(config_path)
    cfg = loader.load()
    
    # Force deep research ON just in case
    cfg._raw["search"]["deep_research"] = True
    cfg._raw["search"]["depth"] = 2
    
    print(f"Config loaded. Deep Research: {cfg._raw['search']['deep_research']}, Depth: {cfg._raw['search']['depth']}")
    
    service = ResearchService(cfg)
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    else:
        topic = "Gemini 3.1"
    
    print(f"Researching topic: {topic}")
    result = await service.research(topic)
    
    print("\n--- Research Complete ---")
    print(f"Findings: {len(result.findings)}")
    print(f"Key Facts: {len(result.key_facts)}")
    print(f"Query Used: {result.query_used}")
    
    print("\n--- Findings Sources ---")
    for f in result.findings:
        print(f"- {f.title} ({f.url})")
        
    print("\n--- Key Facts ---")
    for fact in result.key_facts:
        print(f"- {fact}")

if __name__ == "__main__":
    asyncio.run(main())
