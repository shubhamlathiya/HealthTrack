import datetime
import os
import subprocess
import traceback

from flask import Blueprint, render_template, flash, redirect, url_for, send_from_directory, current_app

from middleware.auth_middleware import token_required
from models import UserRole  # Assuming UserRole is correctly imported

backups_bp = Blueprint('backups', __name__, url_prefix='/backups')

# --- Define ALL static variables here ---
# These paths are now hardcoded. Remember the 'r' for raw string on Windows paths.
STATIC_BACKUP_BASE_DIR = r'S:\github projects\HealthTrack\backup'
STATIC_UPLOADS_BASE_DIR = r'\static\uploads'  # Full path is better

# MySQL Credentials - Hardcoded directly. Highly insecure for production!
STATIC_MYSQL_HOST = 'localhost'
STATIC_MYSQL_USER = 'root'
STATIC_MYSQL_PASSWORD = 'admin'  # REPLACE THIS WITH YOUR ACTUAL PASSWORD!
STATIC_MYSQL_DATABASE = 'healthtrack_demo'

# --- Ensure static directories exist at module load time (or app startup) ---
# This ensures they are ready before any route is called.
if not os.path.exists(STATIC_BACKUP_BASE_DIR):
    try:
        os.makedirs(STATIC_BACKUP_BASE_DIR, exist_ok=True)
        print(f"INFO: Created static backup directory: {STATIC_BACKUP_BASE_DIR}")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to create static backup directory '{STATIC_BACKUP_BASE_DIR}': {e}")
        # In a real app, you might want to raise an error or log a fatal message and exit
        pass  # Allow the app to start, but future operations might fail

if not os.path.exists(STATIC_UPLOADS_BASE_DIR):
    try:
        os.makedirs(STATIC_UPLOADS_BASE_DIR, exist_ok=True)
        print(f"INFO: Created static uploads directory: {STATIC_UPLOADS_BASE_DIR}")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to create static uploads directory '{STATIC_UPLOADS_BASE_DIR}': {e}")
        pass  # Allow the app to start, but future operations might fail


# --- End static directory checks ---


@backups_bp.route('/')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def index(current_user):
    backup_files = []
    try:
        # Use the hardcoded static variable
        if not os.path.exists(STATIC_BACKUP_BASE_DIR):
            # This case should ideally be handled by the startup check above
            flash(f"Backup directory not found: {STATIC_BACKUP_BASE_DIR}", "danger")
            current_app.logger.error(f"Backup directory not found: {STATIC_BACKUP_BASE_DIR}")
            return render_template('backups/list.html', backup_files=[])

        for f in os.listdir(STATIC_BACKUP_BASE_DIR):
            file_path = os.path.join(STATIC_BACKUP_BASE_DIR, f)
            if os.path.isfile(file_path):
                backup_files.append({
                    'name': f,
                    'size': os.path.getsize(file_path),
                    'created_at': datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                })
        backup_files.sort(key=lambda x: x['created_at'], reverse=True)
    except Exception as e:
        flash(f"Error listing backups: {e}", "danger")
        current_app.logger.error(f"Error listing backups: {e}")
    return render_template('backups/list.html', backup_files=backup_files)


@backups_bp.route('/create', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def create_backup(current_user):  # Accept current_user if your decorator provides it
    try:
        # All paths and credentials come from the static variables defined above
        backup_dir = STATIC_BACKUP_BASE_DIR
        static_uploads_dir = STATIC_UPLOADS_BASE_DIR
        mysql_host = STATIC_MYSQL_HOST
        mysql_user = STATIC_MYSQL_USER
        mysql_password = STATIC_MYSQL_PASSWORD
        mysql_database = STATIC_MYSQL_DATABASE

        # Directory existence checks are handled at module load, but a quick re-check is harmless
        if not os.path.exists(backup_dir):
            flash(f"Backup directory not found: {backup_dir}", "danger")
            current_app.logger.error(f"Backup directory not found during create: {backup_dir}")
            return redirect(url_for('backups.index'))
        if not os.path.exists(static_uploads_dir):
            flash(f"Static uploads directory not found: {static_uploads_dir}", "danger")
            current_app.logger.error(f"Static uploads directory not found during create: {static_uploads_dir}")
            return redirect(url_for('backups.index'))

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename_db = f"db_backup_{timestamp}.sql"

        backup_path_db = os.path.join(backup_dir, backup_filename_db)

        # --- MySQL Backup ---
        try:
            mysql_dump_command = [
                'mysqldump',
                f'-h{mysql_host}',
                f'-u{mysql_user}',
                f'-p{mysql_password}',
                mysql_database
            ]
            with open(backup_path_db, 'w') as f:
                subprocess.run(mysql_dump_command, stdout=f, check=True)
            current_app.logger.info(f"Database backup created: {backup_path_db}")
        except subprocess.CalledProcessError as e:
            flash(f"Error creating database backup: MySQL dump failed. {e.stderr.decode()}", "danger")
            current_app.logger.error(f"mysqldump failed: {e.stderr.decode()}")
            return redirect(url_for('backups.index'))
        except FileNotFoundError:
            traceback.print_exc()
            flash("Error: 'mysqldump' command not found. Ensure MySQL client is installed and in your PATH.", "danger")
            current_app.logger.error("mysqldump command not found.")
            return redirect(url_for('backups.index'))

        flash("Backup created successfully!", "success")

    except Exception as e:
        traceback.print_exc()
        flash(f"An unexpected error occurred during backup creation: {e}", "danger")
        current_app.logger.error(f"Unexpected error during backup creation: {e}")

    return redirect(url_for('backups.index'))  # Use url_for for better Flask practice


@backups_bp.route('/download/<filename>')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def download_backup(current_user, filename):
    try:
        # Use the hardcoded static variable
        return send_from_directory(STATIC_BACKUP_BASE_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        flash("Backup file not found.", "danger")
        return redirect(url_for('backups.index'))
    except Exception as e:
        flash(f"Error downloading backup: {e}", "danger")
        current_app.logger.error(f"Error downloading backup '{filename}': {e}")
        return redirect(url_for('backups.index'))


@backups_bp.route('/delete/<filename>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_backup(current_user, filename):
    # Use the hardcoded static variable
    backup_file_path = os.path.join(STATIC_BACKUP_BASE_DIR, filename)
    try:
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)
            flash(f"Backup '{filename}' deleted successfully.", "success")
        else:
            flash("Backup file not found.", "warning")
    except Exception as e:
        flash(f"Error deleting backup '{filename}': {e}", "danger")
        current_app.logger.error(f"Error deleting backup '{filename}': {e}")
    return redirect(url_for('backups.index'))


@backups_bp.route('/restore_confirm/<filename>')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_confirm(current_user, filename):
    # Use the hardcoded static variable
    backup_file_path = os.path.join(STATIC_BACKUP_BASE_DIR, filename)
    if not os.path.exists(backup_file_path):
        flash("Backup file not found for restoration.", "danger")
        return redirect(url_for('backups.index'))
    return render_template('backups/confirm_restore.html', filename=filename)


@backups_bp.route('/restore/<filename>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_backup(current_user, filename):
    """
    Restores the database and optionally static files from a backup.
    WARNING: This operation will overwrite the current database and static files.
    Proceed with extreme caution!
    """
    # Use the hardcoded static variable
    backup_file_path = os.path.join(STATIC_BACKUP_BASE_DIR, filename)

    if not os.path.exists(backup_file_path):
        flash("Backup file not found for restoration.", "danger")
        return redirect(url_for('backups.index'))

    # Check if it's a database backup (.sql) or static file backup (.zip)
    if filename.endswith('.sql'):
        # Restore Database
        try:
            # Use the hardcoded static variables for MySQL
            mysql_restore_command = [
                'mysql',
                f'-h{STATIC_MYSQL_HOST}',
                f'-u{STATIC_MYSQL_USER}',
                f'-p{STATIC_MYSQL_PASSWORD}',
                STATIC_MYSQL_DATABASE
            ]
            with open(backup_file_path, 'r') as f:
                subprocess.run(mysql_restore_command, stdin=f, check=True)
            flash(
                f"Database restored from '{filename}' successfully. Application may need to restart or database connections refreshed.",
                "success")
            current_app.logger.warning(f"Database restored from: {backup_file_path}. This is a critical operation.")

        except subprocess.CalledProcessError as e:
            flash(f"Error restoring database: MySQL restore failed. {e}", "danger")
            current_app.logger.error(f"MySQL restore failed: {e.stderr.decode()}")
        except FileNotFoundError:
            flash(
                "Error restoring database: 'mysql' command not found. Please ensure it is installed and in your PATH.",
                "danger")
            current_app.logger.error("mysql command not found.")
        except Exception as e:
            flash(f"An unexpected error occurred during database restoration: {e}", "danger")
            current_app.logger.error(f"Unexpected error during database restoration: {e}")

    else:
        flash("Unsupported backup file type for restoration.", "warning")

    return redirect(url_for('backups.index'))
