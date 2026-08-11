import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

DB_PATH = os.getenv("DB_PATH", "data/movies.db")

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

HISTORY_LIMIT = 10

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан — заполни .env (см. .env.example)")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY не задан — заполни .env (см. .env.example)")
if not TMDB_API_KEY:
    raise RuntimeError("TMDB_API_KEY не задан — заполни .env (см. .env.example)")
