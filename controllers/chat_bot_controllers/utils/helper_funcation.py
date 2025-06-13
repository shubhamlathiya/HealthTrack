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
        print(f"Chatbot configuration loaded successfully from {config_path}")
        print(f"Loaded config keys: {_cached_chatbot_config.keys()}")
        return _cached_chatbot_config
    except FileNotFoundError:
        print(
            f"ERROR: Chatbot config file NOT FOUND at {config_path}. Please ensure the file exists and the path is correct.")
        _cached_chatbot_config = {}  # Set to empty dict on failure to prevent repeated errors
        return {}  # Return empty dict so app doesn't crash immediately
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from {config_path}. Check file format for errors.")
        print(f"JSON Decoding Error: {e}")
        _cached_chatbot_config = {}
        return {}
    except Exception as e:
        print(f"An unexpected error occurred while loading chatbot config: {e}")
        print(f"Config path attempted: {config_path}")
        _cached_chatbot_config = {}
        return {}


def get_chatbot_options(key, default_options=None):
    config = load_chatbot_config()  # Ensures config is loaded

    retrieved_options = config.get(key, default_options if default_options is not None else [])
    return retrieved_options
