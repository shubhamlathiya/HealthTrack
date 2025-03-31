from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/accounts/income', methods=['GET'], endpoint='income')
def accountIncoms():
    return render_template("admin_templates/accounts/income.html")


@admin.route('/accounts/expenses', methods=['GET'], endpoint='expenses')
def accountExpenss():
    return render_template("admin_templates/accounts/expenses.html")


@admin.route('/accounts/invoices', methods=['GET'], endpoint='invoices')
def accountInvoices():
    return render_template("admin_templates/accounts/invoices.html")


@admin.route('/accounts/payments', methods=['GET'], endpoint='payments')
def accountsPayments():
    return render_template("admin_templates/accounts/payments.html")


@admin.route('/accounts/create-invoice', methods=['GET'], endpoint='create-invoice')
def accounts_create_invoice():
    return render_template("admin_templates/accounts/create-invoice.html")


@admin.route('/accounts/invoice-details', methods=['GET'], endpoint='invoice-details')
def accoutsInvoiceDetails():
    return render_template("admin_templates/accounts/invoice-details.html")
