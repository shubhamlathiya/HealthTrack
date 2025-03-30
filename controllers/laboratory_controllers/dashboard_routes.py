from flask import render_template


from api.laboratory import laboratory


@laboratory.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template("laboratory/laboratory_dashboard_templets.html")
