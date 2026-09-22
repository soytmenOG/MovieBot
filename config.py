import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

DB_PATH = os.getenv("DB_PATH", "data/movies.db")

# Необязательно — адрес SOCKS5-прокси (например "socks5://127.0.0.1:1080"),
# нужен только на серверах, где Telegram/TMDB/OpenRouter не доступны напрямую.
PROXY_URL = os.getenv("PROXY_URL") or None

# Необязательно — адрес n8n-вебхука для команды /feedback (см. проект ClaimsAutomation).
# Если не задан, /feedback просто отвечает пользователю без автоматизации.
FEEDBACK_WEBHOOK_URL = os.getenv("FEEDBACK_WEBHOOK_URL") or None

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

HISTORY_LIMIT = 10

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан — заполни .env (см. .env.example)")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY не задан — заполни .env (см. .env.example)")
if not TMDB_API_KEY:
    raise RuntimeError("TMDB_API_KEY не задан — заполни .env (см. .env.example)")
