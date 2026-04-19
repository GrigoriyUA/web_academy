import secrets

from flask import Flask, request, redirect, url_for, render_template, session

from config import SECRET_KEY, ADMIN_PASSWORD, ADMIN_PANEL_HOST, ADMIN_PANEL_PORT
from database import list_users, update_user_role_status, remove_user

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route('/login', methods=['GET', 'POST'])
def login() -> str:
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        if secrets.compare_digest(password, ADMIN_PASSWORD):
            session['admin_authenticated'] = True
            return redirect(url_for('admin_dashboard'))
        error = 'Невірний пароль. Спробуйте ще раз.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout() -> str:
    session.pop('admin_authenticated', None)
    return redirect(url_for('login'))


@app.route('/admin')
def admin_dashboard() -> str:
    if not session.get('admin_authenticated'):
        return redirect(url_for('login'))
    users = list_users()
    panel_url = f'http://{ADMIN_PANEL_HOST}:{ADMIN_PANEL_PORT}/admin'
    message = request.args.get('message')
    return render_template('admin.html', users=users, panel_url=panel_url, message=message)


@app.route('/admin/update', methods=['POST'])
def update_user_role() -> str:
    if not session.get('admin_authenticated'):
        return redirect(url_for('login'))
    telegram_id = request.form.get('telegram_id')
    role = request.form.get('role')
    status = request.form.get('status')
    if not telegram_id or not telegram_id.isdigit() or role not in ('guest', 'user', 'admin') or status not in ('active', 'pending', 'banned'):
        return redirect(url_for('admin_dashboard', message='Невірні дані.'))
    update_user_role_status(int(telegram_id), role, status)
    return redirect(url_for('admin_dashboard', message='Роль користувача оновлено.'))


@app.route('/admin/remove', methods=['POST'])
def remove_user_view() -> str:
    if not session.get('admin_authenticated'):
        return redirect(url_for('login'))
    telegram_id = request.form.get('telegram_id')
    if telegram_id and telegram_id.isdigit():
        remove_user(int(telegram_id))
    return redirect(url_for('admin_dashboard', message='Користувача видалено.'))


def run_admin_panel() -> None:
    app.run(host=ADMIN_PANEL_HOST, port=ADMIN_PANEL_PORT, debug=False, use_reloader=False)
