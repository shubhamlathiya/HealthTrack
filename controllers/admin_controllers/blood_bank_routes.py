from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.PathConstant import BLOOD_BANK_DONOR, BLOOD_BANK_STOCK, BLOOD_BANK_ISSUED


@admin.route(BLOOD_BANK_DONOR, methods=['GET'], endpoint='blood_bank_donor')
def blood_bank_donor():
    return render_template("admin_templates/blood_bank/blood_donor.html")

@admin.route(BLOOD_BANK_STOCK, methods=['GET'], endpoint='blood_bank_stock')
def blood_bank_stock():
    return render_template("admin_templates/blood_bank/blood_stock.html")

@admin.route(BLOOD_BANK_ISSUED, methods=['GET'], endpoint='blood_bank_issued')
def blood_bank_issued():
    return render_template("admin_templates/blood_bank/blood_issued.html")
