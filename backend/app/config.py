import os
from dotenv import load_dotenv

load_dotenv()

API_KEY: str = os.environ["API_KEY"]
URL: str = os.environ.get("URL", "https://api.sixtyfour.ai")
MAX_CONCURRENT_API_CALLS: int = int(os.environ.get("MAX_CONCURRENT_API_CALLS", "10"))
