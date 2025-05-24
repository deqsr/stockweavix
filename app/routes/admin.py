from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db, Employee
from app.forms import AdminEmployeeForm
from functools import wraps

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Доступ заборонено. Потрібні права адміністратора.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route('/employees')
@admin_required
def list_employees():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    employees = Employee.query.order_by(Employee.EmployeeLastName, Employee.EmployeeFirstName) \
        .paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/employees_list.html', employees_page=employees)


@admin_bp.route('/employees/new', methods=['GET', 'POST'])
@admin_required
def create_employee():
    form = AdminEmployeeForm(request.form if request.method == 'POST' else None,
                             obj_id=None)  # Передаємо obj_id=None для створення
    if form.validate_on_submit():
        new_employee = Employee(
            EmployeeCode=form.employee_code.data,
            EmployeeFirstName=form.employee_first_name.data,
            EmployeeLastName=form.employee_last_name.data,
            EmployeePatronymic=form.employee_patronymic.data if form.employee_patronymic.data else None,
            EmployeeEmail=form.employee_email.data if form.employee_email.data else None,
            EmployeePassport=form.employee_passport.data if form.employee_passport.data else None,
            EmployeePhone=form.employee_phone.data if form.employee_phone.data else None,
            PositionID=form.position_id.data,
            WarehouseID=form.warehouse_id.data,
            IsActive=form.is_active.data,
            IsAdmin=form.is_admin.data
        )
        if form.password.data:
            new_employee.set_password(form.password.data)
        else:
            flash('Увага: Пароль для нового працівника не встановлено. Він не зможе увійти.', 'warning')
            new_employee.PasswordHash = None

        db.session.add(new_employee)
        try:
            db.session.commit()
            flash('Нового працівника успішно створено.', 'success')
            return redirect(url_for('admin_bp.list_employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при створенні працівника: {str(e)}', 'danger')
    elif request.method == 'POST' and not form.validate():
        flash('Будь ласка, виправте помилки у формі.', 'warning')

    return render_template('admin/employee_form.html', form=form, title="Створити працівника", is_edit=False)


@admin_bp.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
@admin_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = AdminEmployeeForm(request.form if request.method == 'POST' else None, obj=employee, obj_id=employee_id)

    if form.validate_on_submit():
        employee.EmployeeCode = form.employee_code.data
        employee.EmployeeFirstName = form.employee_first_name.data
        employee.EmployeeLastName = form.employee_last_name.data
        employee.EmployeePatronymic = form.employee_patronymic.data if form.employee_patronymic.data else None
        employee.EmployeeEmail = form.employee_email.data if form.employee_email.data else None
        employee.EmployeePassport = form.employee_passport.data if form.employee_passport.data else None
        employee.EmployeePhone = form.employee_phone.data if form.employee_phone.data else None
        employee.PositionID = form.position_id.data
        employee.WarehouseID = form.warehouse_id.data
        employee.IsActive = form.is_active.data
        employee.IsAdmin = form.is_admin.data

        if form.password.data:
            employee.set_password(form.password.data)

        try:
            db.session.commit()
            flash('Дані працівника успішно оновлено.', 'success')
            return redirect(url_for('admin_bp.list_employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при оновленні даних працівника: {str(e)}', 'danger')
    elif request.method == 'POST' and not form.validate():
        flash('Будь ласка, виправте помилки у формі.', 'warning')

    return render_template('admin/employee_form.html', form=form, title=f"Редагувати: {employee.EmployeeLastName}",
                           employee_id=employee_id, is_edit=True)