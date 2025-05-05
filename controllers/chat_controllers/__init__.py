from flask import Blueprint

chat = Blueprint("/chat", __name__)

from .chat_routes import *