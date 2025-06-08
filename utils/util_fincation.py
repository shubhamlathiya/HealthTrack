# Allowed extensions for import
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS