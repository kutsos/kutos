import json
import os

_current_lang = "tr"  # Default
_translations = {}

def init(lang_id="tr_TR.UTF-8"):
    global _current_lang, _translations
    
    # Extract 'tr' or 'en' from 'tr_TR.UTF-8'
    _current_lang = lang_id.split('_')[0].lower()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "i18n", f"{_current_lang}.json")
    
    # Fallback to English if file doesn't exist
    if not os.path.exists(json_path):
        json_path = os.path.join(base_dir, "i18n", "en.json")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            _translations = json.load(f)
    except Exception as e:
        print(f"Error loading translation: {e}")
        _translations = {}

def get_text(key, default=None):
    return _translations.get(key, default or key)

# Convenient shorthand
def _(key, default=None):
    return get_text(key, default)
