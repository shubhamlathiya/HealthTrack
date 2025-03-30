import qrcode
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, jsonify, request, send_file
import os

from api.every_one import idCard


#
# app = Flask(__name__)
#
# Folder to store generated ID cards
CARD_FOLDER = "id_cards"
if not os.path.exists(CARD_FOLDER):
    os.makedirs(CARD_FOLDER)

# Generate Barcode for ID Card
def generate_barcode(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    barcode_image = qr.make_image(fill='black', back_color='white')
    return barcode_image

# Generate ID Card
def create_id_card(user):
    card_width, card_height = 600, 400
    card = Image.new("RGB", (card_width, card_height), "white")
    draw = ImageDraw.Draw(card)

    # Fonts (adjust paths for your system)
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
        font_regular = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font_bold = font_regular = ImageFont.load_default()

    # Draw Header
    draw.rectangle([(0, 0), (card_width, 80)], fill="blue")
    draw.text((20, 25), "Hospital Staff ID", fill="white", font=font_bold)

    # Add user details
    draw.text((20, 100), f"Name: {user['name']}", fill="black", font=font_regular)
    draw.text((20, 130), f"Department: {user['department']}", fill="black", font=font_regular)
    draw.text((20, 160), f"Role: {user['role']}", fill="black", font=font_regular)

    # Add Barcode
    barcode = generate_barcode(user['barcode'])
    barcode = barcode.resize((150, 150))
    card.paste(barcode, (400, 200))

    # Save ID Card
    card_path = os.path.join(CARD_FOLDER, f"{user['user_id']}_id_card.png")
    card.save(card_path)
    return card_path

# Example User Data
users = {
    "U001": {
        "user_id": "U001",
        "name": "John Doe",
        "department": "Radiology",
        "role": "Technician",
        "barcode": "U001-RAD"
    }
}

# API to Generate and Retrieve ID Card
@idCard.route('/id-card/<user_id>', methods=['GET'])
def get_id_card(user_id):
    user = users.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    card_path = create_id_card(user)
    return send_file(card_path, mimetype="image/png")
