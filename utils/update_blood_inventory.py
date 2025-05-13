from datetime import datetime, timedelta

from models.bloodModel import BloodInventory
from utils.config import db


def update_blood_inventory(blood_type, units, donation_id=None, is_donation=True):
    """Update blood inventory when donation or transfusion occurs"""
    # For donations, we add to inventory
    # For transfusions/requests, we subtract from inventory

    # Find existing inventory of the same blood type that hasn't expired
    inventory = BloodInventory.query.filter(
        BloodInventory.blood_type == blood_type,
        BloodInventory.expiration_date > datetime.utcnow(),
        BloodInventory.is_deleted == False
    ).order_by(BloodInventory.expiration_date.asc()).first()

    if is_donation:
        # For donations, create new inventory or add to existing
        expiration_date = datetime.utcnow() + timedelta(days=42)  # Blood expires after 42 days

        if inventory and (inventory.units_available + units) <= 10:  # Assuming max 10 units per inventory
            inventory.units_available += units
            if donation_id:
                inventory.donation_id = donation_id
        else:
            new_inventory = BloodInventory(
                blood_type=blood_type,
                units_available=units,
                donation_id=donation_id,
                expiration_date=expiration_date
            )
            db.session.add(new_inventory)
    else:
        # For transfusions/requests, subtract from inventory
        if not inventory or inventory.units_available < units:
            return False  # Not enough blood available

        inventory.units_available -= units
        if inventory.units_available == 0:
            inventory.is_deleted = True
            inventory.deleted_at = datetime.utcnow()

    db.session.commit()
    return True
