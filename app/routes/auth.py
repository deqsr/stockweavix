from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.models import db, Employee
from app.forms import LoginForm

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        # Вхід за EmployeeCode
        employee = Employee.query.filter_by(EmployeeCode=form.employee_code.data).first()
        if employee is None or not employee.check_password(form.password.data):
            flash('Неправильний код працівника або пароль.', 'danger')
            return redirect(url_for('auth_bp.login'))

        if not employee.is_active:
            flash('Ваш акаунт не активовано. Зверніться до адміністратора.', 'warning')
            return redirect(url_for('auth_bp.login'))

        login_user(employee, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')
        return redirect(next_page)
    return render_template('auth/login.html', title='Вхід', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви вийшли з системи.', 'info')
    return redirect(url_for('auth_bp.login'))