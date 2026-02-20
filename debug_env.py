
import os
import sys
from pathlib import Path

print(f"Python executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")

try:
    from dotenv import load_dotenv
    print("Successfully imported load_dotenv")
    
    _HERE = Path(__file__).resolve().parent
    env_path = _HERE / ".env"
    print(f"Looking for .env at: {env_path}")
    print(f"File exists: {env_path.exists()}")
    
    # Try loading explicitly
    loaded = load_dotenv(dotenv_path=env_path, override=True)
    print(f"load_dotenv(explicit) returned: {loaded}")
    
    # Check key
    key = os.environ.get("OPENROUTER_API_KEY")
    print(f"OPENROUTER_API_KEY from env: {key}")
    
    if key:
        print(f"Key length: {len(key)}")
        print(f"First 10 chars: {key[:10]}")
    else:
        print("Key is None")
        
    # debug content
    if env_path.exists():
        print(f"Content of .env: {env_path.read_text()}")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
