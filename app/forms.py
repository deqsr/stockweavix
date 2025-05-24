from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional


class LoginForm(FlaskForm):
    employee_code = StringField('Код працівника', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запам\'ятати мене')
    submit = SubmitField('Увійти')


class AdminEmployeeForm(FlaskForm):
    employee_code = StringField('Код працівника (Логін)', validators=[DataRequired(), Length(min=3, max=50)])
    employee_first_name = StringField('Ім\'я', validators=[DataRequired(), Length(max=255)])
    employee_last_name = StringField('Прізвище', validators=[DataRequired(), Length(max=255)])
    employee_patronymic = StringField('По батькові', validators=[Optional(), Length(max=255)])
    employee_email = StringField('Email', validators=[Optional(), Length(max=255)])
    employee_passport = StringField('Паспорт', validators=[Optional(), Length(max=50)])
    employee_phone = StringField('Телефон', validators=[Optional(), Length(max=50)])

    position_id = SelectField('Посада', coerce=int, validators=[DataRequired(message="Це поле обов'язкове.")])
    warehouse_id = SelectField('Склад', coerce=int, validators=[DataRequired(message="Це поле обов'язкове.")])

    password = PasswordField('Новий пароль',
                             validators=[Optional(), Length(min=6, message="Пароль має бути не менше 6 символів"),
                                         EqualTo('password2', message='Паролі повинні співпадати')])
    password2 = PasswordField('Повторіть новий пароль')
    is_active = BooleanField('Активний (дозволити вхід)')
    is_admin = BooleanField('Адміністратор')
    submit = SubmitField('Зберегти працівника')

    obj_id = None

    def __init__(self, *args, **kwargs):
        self.obj_id = kwargs.get('obj_id', None)
        obj_for_form = kwargs.get('obj')
        super(AdminEmployeeForm, self).__init__(*args, **kwargs)

        from app.models import Position, Warehouse

        self.position_id.choices = [(0, 'Оберіть посаду...')] + \
                                   [(p.PositionID, p.PositionName) for p in
                                    Position.query.order_by(Position.PositionName).all()]
        self.warehouse_id.choices = [(0, 'Оберіть склад...')] + \
                                    [(w.WarehouseID, w.WarehouseName) for w in
                                     Warehouse.query.order_by(Warehouse.WarehouseName).all()]

        if not self.is_submitted():
            if obj_for_form:
                self.employee_code.data = obj_for_form.EmployeeCode
                self.employee_first_name.data = obj_for_form.EmployeeFirstName
                self.employee_last_name.data = obj_for_form.EmployeeLastName
                self.employee_patronymic.data = obj_for_form.EmployeePatronymic
                self.employee_email.data = obj_for_form.EmployeeEmail
                self.employee_passport.data = obj_for_form.EmployeePassport
                self.employee_phone.data = obj_for_form.EmployeePhone
                self.position_id.data = obj_for_form.PositionID
                self.warehouse_id.data = obj_for_form.WarehouseID
                self.is_active.data = obj_for_form.IsActive
                self.is_admin.data = obj_for_form.IsAdmin
            else:
                self.position_id.data = 0
                self.warehouse_id.data = 0
                self.is_active.data = True
                self.is_admin.data = False

    def validate_position_id(self, field):
        if field.data == 0 or field.data is None:
            raise ValidationError('Будь ласка, оберіть посаду.')

    def validate_warehouse_id(self, field):
        if field.data == 0 or field.data is None:
            raise ValidationError('Будь ласка, оберіть склад.')

    def validate_employee_code(self, employee_code_field):
        from app.models import Employee
        query = Employee.query.filter(Employee.EmployeeCode == employee_code_field.data)
        if self.obj_id:
            query = query.filter(Employee.EmployeeID != self.obj_id)
        existing_employee = query.first()
        if existing_employee:
            raise ValidationError('Працівник з таким кодом вже існує.')

    def validate_password(self, field):
        is_creating = not self.obj_id
        if is_creating:
            if not field.data:
                raise ValidationError('Пароль є обов\'язковим для нового працівника.')
            if len(field.data) < 6:
                raise ValidationError('Пароль має бути не менше 6 символів.')
        elif field.data:
            if len(field.data) < 6:
                raise ValidationError('Новий пароль має бути не менше 6 символів.')
            if not self.password2.data:
                self.password2.errors.append('Будь ласка, повторіть новий пароль, якщо ви його змінюєте.')