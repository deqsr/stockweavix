from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_, desc, func
from app.models import db, SupplyContract, Supplier, SupplyStatus, Product, SupplyDetail
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone, date
import decimal

supplies_bp = Blueprint('supplies_bp', __name__, url_prefix='/supplies')


@supplies_bp.route('/')  # Маршрут для списку постачання
def list_supplies():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    search_query_term = request.args.get('search', '')
    status_id_filter = request.args.get('status_id', type=int)
    supplier_id_filter = request.args.get('supplier_id', type=int)
    view_mode = request.args.get('view_mode', 'list')

    filter_date_str = request.args.get('filter_date', '')
    filter_date_obj = None
    if filter_date_str:
        try:
            filter_date_obj = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Некоректний формат дати для фільтра.', 'warning')

    query = SupplyContract.query.options(
        joinedload(SupplyContract.supplier),
        joinedload(SupplyContract.status)
    )

    supplier_joined_for_filter = False

    if search_query_term:
        search_term_int = None
        try:
            search_term_int = int(search_query_term)
        except ValueError:
            pass

        search_conditions = []
        # Пошук за назвою постачальника
        search_conditions.append(Supplier.SupplierName.ilike(f'%{search_query_term}%'))
        if not supplier_joined_for_filter:
            query = query.join(SupplyContract.supplier)  # Явне приєднання supplier
            supplier_joined_for_filter = True

        if search_term_int is not None:
            search_conditions.append(SupplyContract.SupplyID == search_term_int)

        query = query.filter(or_(*search_conditions))

    if status_id_filter:
        query = query.filter(SupplyContract.SupplyStatusID == status_id_filter)

    if supplier_id_filter:
        if not supplier_joined_for_filter:
            query = query.join(SupplyContract.supplier)  # Явне приєднання supplier
        query = query.filter(Supplier.SupplierID == supplier_id_filter)

    if filter_date_obj:
        start_of_day = datetime.combine(filter_date_obj, datetime.min.time())
        end_of_day = datetime.combine(filter_date_obj, datetime.max.time())
        query = query.filter(SupplyContract.CreatedDate.between(start_of_day, end_of_day))

    all_statuses = SupplyStatus.query.order_by(SupplyStatus.StatusName).all()
    all_suppliers = Supplier.query.order_by(Supplier.SupplierName).all()

    pagination = query.order_by(desc(SupplyContract.CreatedDate)).paginate(page=page, per_page=per_page,
                                                                           error_out=False)

    supplies_data = []
    for contract in pagination.items:
        total_items_in_supply = db.session.query(func.sum(SupplyDetail.Quantity)) \
                                    .filter(SupplyDetail.SupplyID == contract.SupplyID).scalar() or 0
        supplies_data.append({
            'id': contract.SupplyID,
            'supplier_name': contract.supplier.SupplierName if contract.supplier else 'N/A',
            'created_date': contract.CreatedDate.strftime('%d.%m.%Y') if contract.CreatedDate else 'N/A',
            'total_price': contract.ContractPrice if contract.ContractPrice is not None else 0.00,
            'status_name': contract.status.StatusName if contract.status else 'N/A',
            'status_class': contract.status.CssClassName if contract.status and contract.status.CssClassName else 'status-default',
            'total_items': total_items_in_supply
        })

    return render_template('supplies_list.html',
                           supplies=supplies_data,
                           pagination=pagination,
                           all_statuses=all_statuses,
                           selected_status_id=status_id_filter,
                           all_suppliers=all_suppliers,
                           selected_supplier_id=supplier_id_filter,
                           search_query=search_query_term,
                           current_view_mode=view_mode,
                           filter_date_str=filter_date_str)


@supplies_bp.route('/new', methods=['GET', 'POST'])
def create_supply_contract():
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id', type=int)
        initial_status_name = "Новий"
        initial_status = SupplyStatus.query.filter_by(StatusName=initial_status_name).first()

        if not initial_status:
            flash(f"Помилка: Не знайдено початковий статус '{initial_status_name}'. Перевірте налаштування статусів.",
                  'danger')
            return redirect(url_for('supplies_bp.list_supplies'))

        if not supplier_id:
            flash('Будь ласка, оберіть постачальника.', 'warning')
            all_suppliers_for_form = Supplier.query.order_by(Supplier.SupplierName).all()
            return render_template('create_supply_form.html',
                                   all_suppliers=all_suppliers_for_form,
                                   form_data=request.form), 400

        new_contract = SupplyContract(
            SupplierID=supplier_id,
            SupplyStatusID=initial_status.SupplyStatusID,
            Description=request.form.get('description', ''),
            CreatedDate=datetime.now(timezone.utc),
            LastUpdated=datetime.now(timezone.utc)
        )
        db.session.add(new_contract)
        try:
            db.session.commit()
            flash(f'Поставку ID {new_contract.SupplyID} успішно створено! Тепер можна додати товари.', 'success')
            return redirect(url_for('supplies_bp.supply_details_view', supply_id=new_contract.SupplyID))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при створенні поставки: {str(e)}', 'danger')
            all_suppliers_for_form = Supplier.query.order_by(Supplier.SupplierName).all()
            return render_template('create_supply_form.html',
                                   all_suppliers=all_suppliers_for_form,
                                   form_data=request.form)

    all_suppliers_for_form = Supplier.query.order_by(Supplier.SupplierName).all()
    return render_template('create_supply_form.html', all_suppliers=all_suppliers_for_form, form_data={})


@supplies_bp.route('/<int:supply_id>/details')
def supply_details_view(supply_id):
    contract = SupplyContract.query.options(
        joinedload(SupplyContract.supplier),
        joinedload(SupplyContract.status),
        joinedload(SupplyContract.details).joinedload(SupplyDetail.product)
    ).get_or_404(supply_id)

    calculated_total_price = 0
    if contract.details:
        for detail in contract.details:
            if detail.UnitPrice and detail.Quantity:

                unit_price = detail.UnitPrice if isinstance(detail.UnitPrice, (int, float, decimal.Decimal)) else 0
                quantity = detail.Quantity if isinstance(detail.Quantity, (int, float, decimal.Decimal)) else 0
                calculated_total_price += unit_price * quantity

    display_price = contract.ContractPrice if contract.ContractPrice is not None else calculated_total_price

    return render_template('supply_details_view.html',
                           contract=contract,
                           display_price=display_price)


@supplies_bp.route('/<int:supply_id>/edit', methods=['GET', 'POST'])
def edit_supply_contract(supply_id):
    contract_to_edit = SupplyContract.query.get_or_404(supply_id)

    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id', type=int)
        status_id = request.form.get('status_id', type=int)
        description = request.form.get('description', '')

        if not supplier_id or not status_id:
            flash('Постачальник та статус є обов\'язковими полями.', 'warning')
            all_suppliers_edit = Supplier.query.order_by(Supplier.SupplierName).all()
            all_statuses_edit = SupplyStatus.query.order_by(SupplyStatus.StatusName).all()

            return render_template('edit_supply_form.html',
                                   contract=contract_to_edit,
                                   all_suppliers=all_suppliers_edit,
                                   all_statuses=all_statuses_edit,
                                   form_data=request.form), 400

        contract_to_edit.SupplierID = supplier_id
        contract_to_edit.SupplyStatusID = status_id
        contract_to_edit.Description = description
        contract_to_edit.LastUpdated = datetime.now(timezone.utc)

        try:
            db.session.commit()
            flash(f'Поставку ID {contract_to_edit.SupplyID} успішно оновлено.', 'success')
            return redirect(url_for('supplies_bp.supply_details_view', supply_id=contract_to_edit.SupplyID))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при оновленні поставки: {str(e)}', 'danger')

            all_suppliers_edit = Supplier.query.order_by(Supplier.SupplierName).all()
            all_statuses_edit = SupplyStatus.query.order_by(SupplyStatus.StatusName).all()
            return render_template('edit_supply_form.html',
                                   contract=contract_to_edit,
                                   all_suppliers=all_suppliers_edit,
                                   all_statuses=all_statuses_edit,
                                   form_data=request.form)


    all_suppliers_edit = Supplier.query.order_by(Supplier.SupplierName).all()
    all_statuses_edit = SupplyStatus.query.order_by(SupplyStatus.StatusName).all()
    form_data_get = {
        'supplier_id': contract_to_edit.SupplierID,
        'status_id': contract_to_edit.SupplyStatusID,
        'description': contract_to_edit.Description or "",
    }
    return render_template('edit_supply_form.html',
                           contract=contract_to_edit,
                           all_suppliers=all_suppliers_edit,
                           all_statuses=all_statuses_edit,
                           form_data=form_data_get)