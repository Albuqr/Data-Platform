import os
from dotenv import load_dotenv
load_dotenv()

LAKEHOUSE_API_URL = os.getenv("LAKEHOUSE_API_URL")
MONITOR_API_URL = os.getenv("MONITOR_API_URL")