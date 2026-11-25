import os
from dotenv import load_dotenv

load_dotenv(override=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN não configurado no .env")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY não configurada no .env")

if not OPENWEATHER_API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY não configurada no .env")