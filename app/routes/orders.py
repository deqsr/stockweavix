from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import desc, or_, and_
from app.models import db, Order, OrderItem, OrderStatus, Client, Product, City
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, date, timezone
import decimal

orders_bp = Blueprint('orders_bp', __name__, url_prefix='/orders')


@orders_bp.route('/')
def list_orders():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    status_id_filter = request.args.get('status_id', type=int)
    client_id_filter = request.args.get('client_id', type=int)
    city_id_filter = request.args.get('city_id', type=int)
    search_term = request.args.get('search', '').strip()
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')

    query = Order.query

    filter_conditions = []
    active_joins = set()

    if status_id_filter:
        filter_conditions.append(Order.OrderStatusID == status_id_filter)

    if client_id_filter:
        if Order.client not in active_joins:  # Використовуємо атрибут зв'язку як ключ
            query = query.join(Order.client)
            active_joins.add(Order.client)
        filter_conditions.append(Client.ClientID == client_id_filter)

    if city_id_filter:
        if Order.city not in active_joins:
            query = query.join(Order.city)
            active_joins.add(Order.city)
        filter_conditions.append(City.CityID == city_id_filter)

    if start_date_str:
        try:
            start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            filter_conditions.append(Order.OrderDate >= start_date_obj)
        except ValueError:
            flash('Некоректний формат початкової дати.', 'warning')
            start_date_str = ''

    if end_date_str:
        try:
            end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            filter_conditions.append(Order.OrderDate <= end_date_obj)
        except ValueError:
            flash('Некоректний формат кінцевої дати.', 'warning')
            end_date_str = ''

    if filter_conditions:
        query = query.filter(and_(*filter_conditions))

    # Застосування пошуку
    if search_term:
        search_or_conditions = []

        try:
            order_id_for_search = int(search_term)
            search_or_conditions.append(Order.OrderID == order_id_for_search)
        except ValueError:
            pass

        search_or_conditions.append(Order.Description.ilike(f"%{search_term}%"))

        if Order.client not in active_joins:
            query = query.outerjoin(Order.client)
            active_joins.add(Order.client)
        if Order.city not in active_joins:
            query = query.outerjoin(Order.city)
            active_joins.add(Order.city)

        search_or_conditions.extend([
            Client.LastName.ilike(f"%{search_term}%"),
            Client.FirstName.ilike(f"%{search_term}%"),
            Client.MiddleName.ilike(f"%{search_term}%"),
            Client.Phone.ilike(f"%{search_term}%"),
            City.CityName.ilike(f"%{search_term}%")
        ])

        if search_or_conditions:
            query = query.filter(or_(*search_or_conditions))

    query = query.options(
        joinedload(Order.client),
        joinedload(Order.status),
        joinedload(Order.city)
    )

    query = query.order_by(desc(Order.OrderDate), desc(Order.OrderID))

    print("\n" + "=" * 30 + " SQL Query for Orders List " + "=" * 30)
    try:
        print(str(query.statement.compile(compile_kwargs={"literal_binds": True})))
    except Exception as e_compile:
        print(f"Error compiling query for printing: {e_compile}")
    print("=" * 80 + "\n")

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    orders_on_page = pagination.items

    all_statuses = OrderStatus.query.order_by(OrderStatus.StatusName).all()
    all_clients = Client.query.order_by(Client.LastName, Client.FirstName).all()
    all_cities = City.query.order_by(City.CityName).all()

    return render_template('orders/orders_list.html',
                           orders=orders_on_page,
                           pagination=pagination,
                           all_statuses=all_statuses,
                           selected_status_id=status_id_filter,
                           all_clients=all_clients,
                           selected_client_id=client_id_filter,
                           all_cities=all_cities,
                           selected_city_id=city_id_filter,
                           search_term=search_term,
                           start_date_form=start_date_str,
                           end_date_form=end_date_str)

# Скопійовано для повноти (без змін відносно версії 15:20)
@orders_bp.route('/new', methods=['GET', 'POST'])
def create_order():
    form_data = request.form if request.method == 'POST' else {}
    all_clients_for_form = Client.query.order_by(Client.LastName, Client.FirstName).all()
    all_cities_for_form = City.query.order_by(City.CityName).all()

    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)
        order_date_str = request.form.get('order_date')
        payment_date_str = request.form.get('payment_date')
        city_id_form = request.form.get('city_id', type=int)
        description_form = request.form.get('description', '')
        shipping_address_form = request.form.get('shipping_address', '')

        status_name_default = "Новий"
        order_status = OrderStatus.query.filter_by(StatusName=status_name_default).first()

        if not order_status:
            flash(f"Помилка: Не знайдено статус за замовчуванням '{status_name_default}'.", 'danger')
            return render_template('orders/create_order_form.html',
                                   all_clients=all_clients_for_form,
                                   all_cities=all_cities_for_form,
                                   current_date=date.today().strftime('%Y-%m-%d'),
                                   form_data=form_data), 500

        if not client_id:
            flash("Будь ласка, оберіть клієнта.", "warning")
            return render_template('orders/create_order_form.html',
                                   all_clients=all_clients_for_form,
                                   all_cities=all_cities_for_form,
                                   current_date=date.today().strftime('%Y-%m-%d'),
                                   form_data=form_data), 400

        try:
            order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date() if order_date_str else date.today()
        except ValueError:
            flash("Некоректний формат дати замовлення.", "warning")
            return render_template('orders/create_order_form.html',
                                   all_clients=all_clients_for_form,
                                   all_cities=all_cities_for_form,
                                   current_date=date.today().strftime('%Y-%m-%d'),
                                   form_data=form_data), 400

        payment_date = None
        if payment_date_str:
            try:
                payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Некоректний формат дати оплати.", "warning")
                return render_template('orders/create_order_form.html',
                                       all_clients=all_clients_for_form,
                                       all_cities=all_cities_for_form,
                                       current_date=date.today().strftime('%Y-%m-%d'),
                                       form_data=form_data), 400

        current_description = description_form
        if shipping_address_form:
            if current_description:
                current_description += f"\n\nАдреса доставки (вказана у формі):\n{shipping_address_form}"
            else:
                current_description = f"Адреса доставки (вказана у формі):\n{shipping_address_form}"

        new_order = Order(
            ClientID=client_id,
            OrderStatusID=order_status.OrderStatusID,
            OrderDate=order_date,
            Description=current_description,
            PaymentDate=payment_date,
            CityID=city_id_form if city_id_form else None
        )

        db.session.add(new_order)
        try:
            db.session.commit()
            flash(f'Замовлення ID {new_order.OrderID} успішно створено. Тепер можна додати товари.', 'success')
            return redirect(url_for('orders_bp.edit_order', order_id=new_order.OrderID))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при створенні замовлення: {str(e)}', 'danger')
            return render_template('orders/create_order_form.html',
                                   all_clients=all_clients_for_form,
                                   all_cities=all_cities_for_form,
                                   current_date=date.today().strftime('%Y-%m-%d'),
                                   form_data=form_data)

    # GET
    current_date_str = date.today().strftime('%Y-%m-%d')
    return render_template('orders/create_order_form.html',
                           all_clients=all_clients_for_form,
                           all_cities=all_cities_for_form,
                           current_date=current_date_str,
                           form_data={'order_date': current_date_str, 'payment_date': ''})


@orders_bp.route('/<int:order_id>/view')
def view_order(order_id):
    order = Order.query.options(
        joinedload(Order.client),
        joinedload(Order.status),
        joinedload(Order.city),
        selectinload(Order.items).joinedload(OrderItem.product)
    ).get_or_404(order_id)
    return render_template('orders/order_details_view.html', order=order)


@orders_bp.route('/<int:order_id>/edit', methods=['GET', 'POST'])
def edit_order(order_id):
    order_to_edit = Order.query.options(
        selectinload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.city)
    ).get_or_404(order_id)

    all_clients_for_form = Client.query.order_by(Client.LastName, Client.FirstName).all()
    all_statuses_for_form = OrderStatus.query.order_by(OrderStatus.StatusName).all()
    all_products_for_form = Product.query.order_by(Product.ProductName).all()
    all_cities_for_form = City.query.order_by(City.CityName).all()

    if request.method == 'POST':
        form_data_post = request.form
        try:
            client_id_form = request.form.get('client_id', type=int)
            status_id_form = request.form.get('status_id', type=int)
            order_date_str = request.form.get('order_date')
            payment_date_str = request.form.get('payment_date')
            city_id_form = request.form.get('city_id', type=int)

            if not client_id_form or not status_id_form or not order_date_str:
                flash('Клієнт, статус та дата замовлення є обов\'язковими.', 'warning')
                return render_template('orders/edit_order_form.html',
                                       order=order_to_edit,
                                       all_clients=all_clients_for_form,
                                       all_statuses=all_statuses_for_form,
                                       all_products=all_products_for_form,
                                       all_cities=all_cities_for_form,
                                       form_data=form_data_post), 400

            order_to_edit.ClientID = client_id_form
            order_to_edit.OrderStatusID = status_id_form
            order_to_edit.OrderDate = datetime.strptime(order_date_str, '%Y-%m-%d').date()
            order_to_edit.CityID = city_id_form if city_id_form else None

            if payment_date_str:
                try:
                    order_to_edit.PaymentDate = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash("Некоректний формат дати оплати. Зміни для дати оплати не збережено.", "warning")
                    order_to_edit.PaymentDate = None
            else:
                order_to_edit.PaymentDate = None

            description_from_form = request.form.get('description', '')
            shipping_address_from_form = request.form.get('shipping_address', '')
            final_description = description_from_form
            if shipping_address_from_form:
                if final_description:
                    final_description += f"\n\nАдреса доставки (вказана у формі):\n{shipping_address_from_form}"
                else:
                    final_description = f"Адреса доставки (вказана у формі):\n{shipping_address_from_form}"
            order_to_edit.Description = final_description
            order_to_edit.LastUpdated = datetime.now(timezone.utc)

        except ValueError as ve:
            flash(f'Некоректний формат дати: {ve}', 'warning')
            return render_template('orders/edit_order_form.html',
                                   order=order_to_edit, all_clients=all_clients_for_form,
                                   all_statuses=all_statuses_for_form, all_products=all_products_for_form,
                                   all_cities=all_cities_for_form,
                                   form_data=form_data_post), 400
        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при оновленні даних замовлення: {e}", "danger")
            order_to_edit = Order.query.options(
                selectinload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.city)
            ).get_or_404(order_id)
            return render_template('orders/edit_order_form.html', order=order_to_edit, all_clients=all_clients_for_form,
                                   all_statuses=all_statuses_for_form, all_products=all_products_for_form,
                                   all_cities=all_cities_for_form,
                                   form_data=form_data_post), 500

        # Обробка існуючих товарів
        existing_items_map = {item.OrderItemID: item for item in order_to_edit.items}
        form_keys_for_existing_items = [k for k in request.form if k.startswith('items-')]
        ids_of_items_in_form = set()
        for key in form_keys_for_existing_items:
            if key.endswith('-product_id'):
                try:
                    item_id_str = key.split('-')[1]
                    if item_id_str.isdigit():
                        ids_of_items_in_form.add(int(item_id_str))
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
                    quantity_str = request.form.get(prefix + 'quantity', '0')
                    unit_price_str = request.form.get(prefix + 'unit_price', '0.00').replace(',', '.')
                    quantity_val = int(quantity_str)
                    unit_price_val = decimal.Decimal(unit_price_str)
                    if quantity_val <= 0:
                        db.session.delete(item_to_process)
                        flash(
                            f"Кількість для позиції товару {item_to_process.product.ProductName if item_to_process.product else 'ID ' + str(item_to_process.ProductID)} була 0 або менше, позицію видалено.",
                            "info")
                        continue
                    if unit_price_val < decimal.Decimal('0'): unit_price_val = decimal.Decimal('0.00')
                    item_to_process.Quantity = quantity_val
                    item_to_process.UnitPrice = unit_price_val
                except (ValueError, decimal.InvalidOperation) as e:
                    db.session.rollback()
                    flash(f"Некоректні дані для оновлення позиції ID {item_id}: {e}", "warning")
                    order_to_edit = Order.query.options(selectinload(Order.items).joinedload(OrderItem.product),
                                                        joinedload(Order.city)).get_or_404(order_id)
                    return render_template('orders/edit_order_form.html', order=order_to_edit,
                                           all_clients=all_clients_for_form, all_statuses=all_statuses_for_form,
                                           all_products=all_products_for_form, all_cities=all_cities_for_form,
                                           form_data=form_data_post), 400

        # Додавання нових товарів
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
                unit_price_str = data_dict.get('unit_price', '').replace(',', '.')
                product_for_price = Product.query.get(product_id)
                if unit_price_str:
                    unit_price = decimal.Decimal(unit_price_str)
                elif product_for_price and product_for_price.Price is not None:
                    unit_price = product_for_price.Price
                else:
                    flash(
                        f"Для нового товару (продукт ID {product_id}) не вказана ціна і не знайдена ціна за замовчуванням. Товар не додано.",
                        "warning")
                    continue
                if quantity <= 0:
                    flash(f"Кількість для нового товару (продукт ID {product_id}) має бути більше 0. Товар не додано.",
                          "warning")
                    continue
                if unit_price < decimal.Decimal('0'): unit_price = decimal.Decimal('0.00')
                new_order_item = OrderItem(OrderID=order_to_edit.OrderID, ProductID=product_id, Quantity=quantity,
                                           UnitPrice=unit_price)
                db.session.add(new_order_item)
            except (ValueError, decimal.InvalidOperation) as e:
                db.session.rollback()
                flash(f"Некоректні дані для нового товару в замовленні (форма індекс {_form_idx}): {e}", "warning")
                order_to_edit = Order.query.options(selectinload(Order.items).joinedload(OrderItem.product),
                                                    joinedload(Order.city)).get_or_404(order_id)
                return render_template('orders/edit_order_form.html', order=order_to_edit, all_clients=all_clients_for_form,
                                       all_statuses=all_statuses_for_form, all_products=all_products_for_form,
                                       all_cities=all_cities_for_form, form_data=form_data_post), 400

        try:
            db.session.commit()
            flash(f'Замовлення ID {order_to_edit.OrderID} успішно оновлено.', 'success')
            return redirect(url_for('orders_bp.view_order', order_id=order_to_edit.OrderID))
        except Exception as e_commit:
            db.session.rollback()
            flash(f'Помилка при збереженні замовлення: {str(e_commit)}', 'danger')
            order_to_edit = Order.query.options(selectinload(Order.items).joinedload(OrderItem.product),
                                                joinedload(Order.city)).get_or_404(order_id)
            return render_template('orders/edit_order_form.html',
                                   order=order_to_edit,
                                   all_clients=all_clients_for_form,
                                   all_statuses=all_statuses_for_form,
                                   all_products=all_products_for_form,
                                   all_cities=all_cities_for_form,
                                   form_data=form_data_post)

    # GET
    initial_shipping_address = ""
    if order_to_edit.client and order_to_edit.client.Address:
        if order_to_edit.client.Address.strip().lower() != 'не вказано':  # Не показуємо "Не вказано" як адресу доставки
            initial_shipping_address = order_to_edit.client.Address

    form_data_get = {
        'client_id': order_to_edit.ClientID,
        'status_id': order_to_edit.OrderStatusID,
        'order_date': order_to_edit.OrderDate.strftime('%Y-%m-%d') if order_to_edit.OrderDate else '',
        'payment_date': order_to_edit.PaymentDate.strftime('%Y-%m-%d') if order_to_edit.PaymentDate else '',
        'city_id': order_to_edit.CityID if order_to_edit.CityID else '',
        'description': order_to_edit.Description or '',
        'shipping_address': initial_shipping_address
    }
    return render_template('orders/edit_order_form.html',
                           order=order_to_edit,
                           all_clients=all_clients_for_form,
                           all_statuses=all_statuses_for_form,
                           all_products=all_products_for_form,
                           all_cities=all_cities_for_form,
                           form_data=form_data_get)