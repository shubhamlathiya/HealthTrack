from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ACCOUNTS_INCOME, ACCOUNTS_EXPENSES, ACCOUNTS_INVOICES, \
    ACCOUNTS_PAYMENTS, \
    ACCOUNTS_CREATE_INVOICE, ACCOUNTS_INVOICES_DETAILS


@admin.route(ACCOUNTS_INCOME, methods=['GET'], endpoint='income')
def accountIncoms():
    return render_template("admin_templates/accounts/income.html")


@admin.route(ACCOUNTS_EXPENSES, methods=['GET'], endpoint='expenses')
def accountExpenss():
    return render_template("admin_templates/accounts/expenses.html")


@admin.route(ACCOUNTS_INVOICES, methods=['GET'], endpoint='invoices')
def accountInvoices():
    return render_template("admin_templates/accounts/invoices.html")


@admin.route(ACCOUNTS_PAYMENTS, methods=['GET'], endpoint='payments')
def accountsPayments():
    return render_template("admin_templates/accounts/payments.html")


@admin.route(ACCOUNTS_CREATE_INVOICE, methods=['GET'], endpoint='create-invoice')
def accounts_create_invoice():
    return render_template("admin_templates/accounts/create-invoice.html")


@admin.route(ACCOUNTS_INVOICES_DETAILS, methods=['GET'], endpoint='invoice-details')
def accoutsInvoiceDetails():
    return render_template("admin_templates/accounts/invoice-details.html")
