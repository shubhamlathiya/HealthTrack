from flask import Blueprint

chatbot = Blueprint("bot", __name__)


from .chat_bot_routes import *