from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import desc, or_
from app.models import db, Order, OrderItem, OrderStatus, Client, Product, City
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, date, timezone
import decimal

orders_bp = Blueprint('orders_bp', __name__, url_prefix='/orders')



def recalculate_order_total(order_id):
    order = Order.query.get(order_id)
    if order:
        current_total = decimal.Decimal('0.00')
        for item in order.items:
            if item.Quantity is not None and item.UnitPrice is not None:
                current_total += decimal.Decimal(str(item.Quantity)) * decimal.Decimal(str(item.UnitPrice))
        order.OrderTotal = current_total


@orders_bp.route('/')
def list_orders():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    # Фільтри
    status_id_filter = request.args.get('status_id', type=int)
    client_id_filter = request.args.get('client_id', type=int)
    search_term = request.args.get('search', '').strip()

    query = Order.query.options(
        joinedload(Order.client),
        joinedload(Order.status)
    ).order_by(desc(Order.OrderDate), desc(Order.OrderID))  # Спочатку новіші за датою, потім за ID

    if status_id_filter:
        query = query.filter(Order.OrderStatusID == status_id_filter)

    if client_id_filter:
        query = query.filter(Order.ClientID == client_id_filter)

    if search_term:
        try:
            order_id_search = int(search_term)
            query = query.filter(Order.OrderID == order_id_search)
        except ValueError:
            # Пошук за іменем клієнта або описом
            query = query.join(Client, Order.ClientID == Client.ClientID, isouter=True).filter(
                or_(
                    Client.LastName.ilike(f"%{search_term}%"),
                    Client.FirstName.ilike(f"%{search_term}%"),
                    Order.Description.ilike(f"%{search_term}%")
                )
            )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    orders_on_page = pagination.items

    all_statuses = OrderStatus.query.order_by(OrderStatus.StatusName).all()
    all_clients = Client.query.order_by(Client.LastName, Client.FirstName).all()

    return render_template('orders_list.html',
                           orders=orders_on_page,
                           pagination=pagination,
                           all_statuses=all_statuses,
                           selected_status_id=status_id_filter,
                           all_clients=all_clients,
                           selected_client_id=client_id_filter,
                           search_term=search_term)


@orders_bp.route('/new', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)


        status_name_default = "Новий"  # Або інший ваш дефолтний статус
        order_status = OrderStatus.query.filter_by(StatusName=status_name_default).first()

        if not order_status:
            flash(f"Помилка: Не знайдено статус за замовчуванням '{status_name_default}'.", 'danger')
            all_clients_for_form = Client.query.order_by(Client.LastName, Client.FirstName).all()
            return render_template('create_order_form.html',
                                   all_clients=all_clients_for_form,
                                   # all_cities=all_cities_for_form,
                                   form_data=request.form), 500

        if not client_id:
            flash("Будь ласка, оберіть клієнта.", "warning")
            all_clients_for_form = Client.query.order_by(Client.LastName, Client.FirstName).all()
            return render_template('create_order_form.html',
                                   all_clients=all_clients_for_form,
                                   form_data=request.form), 400

        new_order = Order(
            ClientID=client_id,
            OrderStatusID=order_status.OrderStatusID,
            OrderDate=datetime.strptime(request.form.get('order_date'), '%Y-%m-%d').date() if request.form.get(
                'order_date') else date.today(),
            Description=request.form.get('description', ''),
            ShippingAddress=request.form.get('shipping_address', ''),
            OrderTotal=decimal.Decimal('0.00')
        )
        db.session.add(new_order)
        try:
            db.session.commit()
            flash(f'Замовлення ID {new_order.OrderID} успішно створено. Тепер можна додати товари.', 'success')
            return redirect(url_for('orders_bp.edit_order', order_id=new_order.OrderID))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при створенні замовлення: {str(e)}', 'danger')
            all_clients_for_form = Client.query.order_by(Client.LastName, Client.FirstName).all()
            return render_template('create_order_form.html',
                                   all_clients=all_clients_for_form,
                                   form_data=request.form)

    # GET
    all_clients_for_form = Client.query.order_by(Client.LastName, Client.FirstName).all()
    # all_cities_for_form = City.query.order_by(City.CityName).all()
    current_date = date.today().strftime('%Y-%m-%d')
    return render_template('create_order_form.html',
                           all_clients=all_clients_for_form,
                           current_date=current_date,
                           form_data={})


@orders_bp.route('/<int:order_id>/view')
def view_order(order_id):
    order = Order.query.options(
        joinedload(Order.client),
        joinedload(Order.status),
        # joinedload(Order.city)
        selectinload(Order.items).joinedload(OrderItem.product)  # Важливо для товарів
    ).get_or_404(order_id)

    return render_template('order_details_view.html', order=order)

@orders_bp.route('/<int:order_id>/edit', methods=['GET', 'POST'])
def edit_order(order_id):
    order_to_edit = Order.query.options(
        selectinload(Order.items).joinedload(OrderItem.product)  # товари
    ).get_or_404(order_id)

    all_clients_for_form = Client.query.order_by(Client.LastName, Client.FirstName).all()
    all_statuses_for_form = OrderStatus.query.order_by(OrderStatus.StatusName).all()
    all_products_for_form = Product.query.order_by(Product.ProductName).all()  # додавання товарів

    if request.method == 'POST':
        # 1. Оновлення основних даних замовлення
        try:
            client_id_form = request.form.get('client_id', type=int)
            status_id_form = request.form.get('status_id', type=int)
            order_date_str = request.form.get('order_date')

            if not client_id_form or not status_id_form or not order_date_str:
                flash('Клієнт, статус та дата замовлення є обов\'язковими.', 'warning')
                # форма з поточними даними для виправлення
                return render_template('edit_order_form.html',
                                       order=order_to_edit,
                                       all_clients=all_clients_for_form,
                                       all_statuses=all_statuses_for_form,
                                       all_products=all_products_for_form,
                                       form_data=request.form), 400  # Bad request

            order_to_edit.ClientID = client_id_form
            order_to_edit.OrderStatusID = status_id_form
            order_to_edit.OrderDate = datetime.strptime(order_date_str, '%Y-%m-%d').date()
            order_to_edit.Description = request.form.get('description', order_to_edit.Description or '')
            order_to_edit.ShippingAddress = request.form.get('shipping_address', order_to_edit.ShippingAddress or '')
            order_to_edit.LastUpdated = datetime.now(timezone.utc)
        except ValueError:
            flash('Некоректний формат дати замовлення.', 'warning')
            return render_template('edit_order_form.html',
                                   order=order_to_edit,
                                   all_clients=all_clients_for_form,
                                   all_statuses=all_statuses_for_form,
                                   all_products=all_products_for_form,
                                   form_data=request.form), 400
        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при оновленні даних замовлення: {e}", "danger")
            # Перезавантажуємо для чистоти
            order_to_edit = Order.query.options(selectinload(Order.items).joinedload(OrderItem.product)).get_or_404(
                order_id)
            return render_template('edit_order_form.html', order=order_to_edit, all_clients=all_clients_for_form,
                                   all_statuses=all_statuses_for_form, all_products=all_products_for_form,
                                   form_data=request.form), 500

        # 2. Обробка існуючих товарів в замовленні (OrderItem)
        existing_items_map = {item.OrderItemID: item for item in order_to_edit.items}
        form_keys_for_existing_items = [k for k in request.form if k.startswith('items-')]
        ids_of_items_in_form = set()

        for key in form_keys_for_existing_items:
            if key.endswith('-product_id'):  # ID позиції
                try:
                    item_id = int(key.split('-')[1])
                    ids_of_items_in_form.add(item_id)
                except (IndexError, ValueError):
                    continue

        for item_id in ids_of_items_in_form:
            item_to_process = existing_items_map.get(item_id)
            if not item_to_process: continue

            prefix = f'items-{item_id}-'
            if request.form.get(prefix + 'delete'):
                db.session.delete(item_to_process)
            else:
                try:
                    # product_id_val = request.form.get(prefix + 'product_id', type=int)
                    quantity_str = request.form.get(prefix + 'quantity', '0')
                    unit_price_str = request.form.get(prefix + 'unit_price', '0.00').replace(',', '.')

                    quantity_val = int(quantity_str)
                    unit_price_val = decimal.Decimal(unit_price_str)

                    if quantity_val <= 0:
                        db.session.delete(item_to_process)
                        flash(f"Кількість для позиції {item_id} була 0 або менше, позицію видалено.", "info")
                        continue
                    if unit_price_val < decimal.Decimal('0'): unit_price_val = decimal.Decimal('0.00')

                    # item_to_process.ProductID = product_id_val
                    item_to_process.Quantity = quantity_val
                    item_to_process.UnitPrice = unit_price_val
                except (ValueError, decimal.InvalidOperation) as e:
                    db.session.rollback()
                    flash(f"Некоректні дані для оновлення позиції ID {item_id}: {e}", "warning")
                    order_to_edit = Order.query.options(
                        selectinload(Order.items).joinedload(OrderItem.product)).get_or_404(order_id)
                    return render_template('edit_order_form.html', order=order_to_edit,
                                           all_clients=all_clients_for_form, all_statuses=all_statuses_for_form,
                                           all_products=all_products_for_form, form_data=request.form), 400

        # 3. Додавання нових товарів (OrderItem)
        new_items_form_data = {}
        for key, value in request.form.items():
            if key.startswith('new_items-'):
                parts = key.split('-')
                if len(parts) == 3:
                    index_str, field_name = parts[1], parts[2]
                    if index_str not in new_items_form_data: new_items_form_data[index_str] = {'_form_index': index_str}
                    new_items_form_data[index_str][field_name] = value

        for _form_idx, data_dict in new_items_form_data.items():
            product_id_str = data_dict.get('product_id')
            if not product_id_str or not product_id_str.strip(): continue

            try:
                product_id = int(product_id_str)
                quantity = int(data_dict.get('quantity', '1'))

                # Ціна з картки товару, якщо не вказана у формі
                unit_price_str = data_dict.get('unit_price', '').replace(',', '.')
                product_for_price = Product.query.get(product_id)

                if unit_price_str:
                    unit_price = decimal.Decimal(unit_price_str)
                elif product_for_price and product_for_price.Price is not None:
                    unit_price = product_for_price.Price
                else:
                    unit_price = decimal.Decimal('0.00')  # flash помилка, якщо ціна не знайдена

                if quantity <= 0: continue
                if unit_price < decimal.Decimal('0'): unit_price = decimal.Decimal('0.00')

                new_order_item = OrderItem(
                    OrderID=order_to_edit.OrderID,  # ID замовлення
                    ProductID=product_id,
                    Quantity=quantity,
                    UnitPrice=unit_price
                )
                db.session.add(new_order_item)
            except (ValueError, decimal.InvalidOperation) as e:
                db.session.rollback()
                flash(f"Некоректні дані для нового товару в замовленні (форма індекс {_form_idx}): {e}", "warning")
                order_to_edit = Order.query.options(selectinload(Order.items).joinedload(OrderItem.product)).get_or_404(
                    order_id)
                return render_template('edit_order_form.html', order=order_to_edit, all_clients=all_clients_for_form,
                                       all_statuses=all_statuses_for_form, all_products=all_products_for_form,
                                       form_data=request.form), 400

        # 4. Перерахунок OrderTotal
        try:
            db.session.flush()  # Щоб зміни в order_to_edit.items були доступні
            order_to_edit.calculate_total()  # Використовуємо метод моделі
        except Exception as e_calc:
            db.session.rollback()
            flash(f"Помилка під час перерахунку суми замовлення: {e_calc}", "danger")
            order_to_edit = Order.query.options(selectinload(Order.items).joinedload(OrderItem.product)).get_or_404(
                order_id)
            return render_template('edit_order_form.html', order=order_to_edit, all_clients=all_clients_for_form,
                                   all_statuses=all_statuses_for_form, all_products=all_products_for_form,
                                   form_data=request.form), 500

        # 5. Збереження
        try:
            db.session.commit()
            flash(f'Замовлення ID {order_to_edit.OrderID} успішно оновлено.', 'success')
            return redirect(url_for('orders_bp.view_order', order_id=order_to_edit.OrderID))  # Редірект на перегляд
        except Exception as e_commit:
            db.session.rollback()
            flash(f'Помилка при збереженні замовлення: {str(e_commit)}', 'danger')
            order_to_edit = Order.query.options(selectinload(Order.items).joinedload(OrderItem.product)).get_or_404(
                order_id)
            return render_template('edit_order_form.html',
                                   order=order_to_edit,
                                   all_clients=all_clients_for_form,
                                   all_statuses=all_statuses_for_form,
                                   all_products=all_products_for_form,
                                   form_data=request.form)

    # GET
    form_data_get = {
        'client_id': order_to_edit.ClientID,
        'status_id': order_to_edit.OrderStatusID,
        'order_date': order_to_edit.OrderDate.strftime('%Y-%m-%d') if order_to_edit.OrderDate else '',
        'description': order_to_edit.Description or '',
        'shipping_address': order_to_edit.ShippingAddress or ''
    }
    return render_template('edit_order_form.html',
                           order=order_to_edit,
                           all_clients=all_clients_for_form,
                           all_statuses=all_statuses_for_form,
                           all_products=all_products_for_form,
                           form_data=form_data_get)