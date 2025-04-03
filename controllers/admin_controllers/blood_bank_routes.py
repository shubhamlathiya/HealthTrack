from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/blood-bank/donor', methods=['GET'], endpoint='blood_bank_donor')
def blood_bank_donor():
    return render_template("admin_templates/blood_bank/blood_donor.html")

@admin.route('/blood-bank/stock', methods=['GET'], endpoint='blood_bank_stock')
def blood_bank_stock():
    return render_template("admin_templates/blood_bank/blood_stock.html")

@admin.route('/blood-bank/issued', methods=['GET'], endpoint='blood_bank_issued')
def blood_bank_issued():
    return render_template("admin_templates/blood_bank/blood_issued.html")
