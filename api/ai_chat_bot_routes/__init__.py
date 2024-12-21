from flask import Blueprint

# Initialize the 'client' blueprint
chatbot = Blueprint('chatbot', __name__)

# Import views from other modules (dashboard, orders)
from .main_chat_bot import *
