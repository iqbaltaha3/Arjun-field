import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = 'Arjun Field'
DB_PATH = os.getenv('ARJUN_FIELD_DB', 'arjun_field.db')
LOCATION_INTERVAL_SECONDS = 180
LOCATION_STALE_SECONDS = 420
SESSION_STALE_SECONDS = 420

ADMIN_ID = os.getenv('ADMIN_ID', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'change-me-now')

SARVAM_API_KEY = os.getenv('SARVAM_API_KEY', '')
SARVAM_STT_MODEL = os.getenv('SARVAM_STT_MODEL', 'saaras:v4')
SARVAM_STT_MODE = os.getenv('SARVAM_STT_MODE', 'transcribe')

# Arjun Field LLM: Groq
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'groq').lower()
LLM_MODEL = os.getenv('LLM_MODEL', 'openai/gpt-oss-20b')
LLM_API_KEY = os.getenv('GROQ_API_KEY', '') or os.getenv('LLM_API_KEY', '')
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.groq.com/openai/v1')
