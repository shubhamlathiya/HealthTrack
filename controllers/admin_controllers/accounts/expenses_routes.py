from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ACCOUNTS_EXPENSES


@admin.route(ACCOUNTS_EXPENSES, methods=['GET'], endpoint='expenses')
def accountExpenss():
    return render_template("admin_templates/accounts/expenses.html")
