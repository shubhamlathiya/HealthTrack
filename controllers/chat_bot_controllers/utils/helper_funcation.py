import os
import json

def load_chatbot_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Correct path: go into 'data' folder from current_dir
    config_path = os.path.join(current_dir, '../data', 'chatbot_config.json')  # <-- MODIFY THIS LINE

    # config_path = 'data/chatbot_config.json'

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            _cached_chatbot_config = json.load(f)

        return _cached_chatbot_config
    except FileNotFoundError:
        _cached_chatbot_config = {}  # Set to empty dict on failure to prevent repeated errors
        return {}  # Return empty dict so app doesn't crash immediately
    except json.JSONDecodeError as e:
        _cached_chatbot_config = {}
        return {}
    except Exception as e:
        _cached_chatbot_config = {}
        return {}


def get_chatbot_options(key, default_options=None):
    config = load_chatbot_config()  # Ensures config is loaded

    retrieved_options = config.get(key, default_options if default_options is not None else [])
    return retrieved_options
