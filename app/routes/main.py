# app/routes/main.py
from flask import Blueprint, render_template, request, jsonify, current_app  # Додано jsonify
from sqlalchemy import func, desc
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from app.models import (
    db,
    Order,
    OrderItem,
    Product,
    ProductCategory,
    Manufacturer,
    SupplyContract,
    SupplyStatus,
    City,
    Zone,
    ZoneOccupancyView
)

main_bp = Blueprint('main', __name__)


def get_growth_class(value):
    if value is None:
        return "text-growth-neutral"
    if value == 0:  # Якщо зміна 0%
        return "text-growth-neutral"
    elif value > 0:
        return "text-growth-positive"
    else:  # value < 0
        return "text-growth-negative"


@main_bp.route('/api/chart-data')
def api_chart_data():
    today_dt = datetime.utcnow().date()
    default_start_date_chart = today_dt - timedelta(days=29)
    default_end_date_chart = today_dt

    start_date_str = request.args.get('start_date', default_start_date_chart.strftime('%Y-%m-%d'))
    end_date_str = request.args.get('end_date', default_end_date_chart.strftime('%Y-%m-%d'))
    category_id_str = request.args.get('category_id', '')
    manufacturer_id_str = request.args.get('manufacturer_id', '')

    try:
        start_date_chart_filter = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date_chart_filter = default_start_date_chart
    try:
        end_date_chart_filter = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        end_date_chart_filter = default_end_date_chart

    if end_date_chart_filter < start_date_chart_filter:

        end_date_chart_filter = start_date_chart_filter

    selected_category_id_chart = int(category_id_str) if category_id_str.isdigit() else None
    selected_manufacturer_id_chart = int(manufacturer_id_str) if manufacturer_id_str.isdigit() else None

    query_chart_data_base = db.session.query(
        Order.OrderDate,
        func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), 0).label('daily_sales_sum'),
        func.coalesce(func.sum(OrderItem.Quantity), 0).label('daily_quantity_sum')
    ).join(OrderItem, Order.OrderID == OrderItem.OrderID) \
        .join(Product, Product.ProductID == OrderItem.ProductID) \
        .filter(Order.OrderDate.between(start_date_chart_filter, end_date_chart_filter))

    if selected_category_id_chart:
        query_chart_data_base = query_chart_data_base.filter(Product.ProductCategoryID == selected_category_id_chart)
    if selected_manufacturer_id_chart:
        query_chart_data_base = query_chart_data_base.filter(Product.ManufacturerID == selected_manufacturer_id_chart)

    sales_and_qty_by_day_raw = query_chart_data_base.group_by(Order.OrderDate).order_by(Order.OrderDate).all()

    chart_labels_api = []
    chart_sales_values_api = []
    chart_quantity_values_api = []
    data_map_chart_api = {row.OrderDate: (float(row.daily_sales_sum), int(row.daily_quantity_sum)) for row in
                          sales_and_qty_by_day_raw}

    current_day_in_loop_api = start_date_chart_filter
    while current_day_in_loop_api <= end_date_chart_filter:
        chart_labels_api.append(current_day_in_loop_api.strftime('%d-%m'))
        sales_val, qty_val = data_map_chart_api.get(current_day_in_loop_api, (0.0, 0))
        chart_sales_values_api.append(sales_val)
        chart_quantity_values_api.append(qty_val)
        current_day_in_loop_api += timedelta(days=1)

    return jsonify({
        'labels': chart_labels_api,
        'sales_values': chart_sales_values_api,
        'quantity_values': chart_quantity_values_api
    })


@main_bp.route('/')
def dashboard():
    today_dt = datetime.utcnow().date()
    default_start_date_chart = today_dt - timedelta(days=29)
    default_end_date_chart = today_dt

    # параметри фільтрів з URL для початкового завантаження
    start_date_chart_form_val_str = request.args.get('start_date_chart', default_start_date_chart.strftime('%Y-%m-%d'))
    end_date_chart_form_val_str = request.args.get('end_date_chart', default_end_date_chart.strftime('%Y-%m-%d'))
    category_id_chart_form_str = request.args.get('category_id_chart', '')
    manufacturer_id_chart_form_str = request.args.get('manufacturer_id_chart', '')

    try:
        initial_start_date = datetime.strptime(start_date_chart_form_val_str, '%Y-%m-%d').date()
    except ValueError:
        initial_start_date = default_start_date_chart
    try:
        initial_end_date = datetime.strptime(end_date_chart_form_val_str, '%Y-%m-%d').date()
    except ValueError:
        initial_end_date = default_end_date_chart

    if initial_end_date < initial_start_date:
        initial_end_date = initial_start_date

    selected_category_id_chart_form = int(category_id_chart_form_str) if category_id_chart_form_str.isdigit() else None
    selected_manufacturer_id_chart_form = int(
        manufacturer_id_chart_form_str) if manufacturer_id_chart_form_str.isdigit() else None

    # Дані для випадаючих списків фільтрів
    categories_filter_data = ProductCategory.query.order_by(ProductCategory.CategoryName).all()
    manufacturers_filter_data = Manufacturer.query.order_by(Manufacturer.ManufacturerName).all()

    # --- KPI Calculations ---
    today_kpi_logic = datetime.utcnow().date()
    if today_kpi_logic.day > 15:
        start_current_kpi_period = today_kpi_logic.replace(day=1)
    else:
        start_current_kpi_period = (today_kpi_logic.replace(day=1) - timedelta(days=1)).replace(day=1)
    end_current_kpi_period = (start_current_kpi_period + relativedelta(months=1)) - timedelta(days=1)
    start_prev_kpi_period = start_current_kpi_period - relativedelta(months=1)
    end_prev_kpi_period = (start_prev_kpi_period + relativedelta(months=1)) - timedelta(days=1)

    curr_orders_kpi = db.session.query(func.count(Order.OrderID)) \
                          .filter(Order.OrderDate.between(start_current_kpi_period, end_current_kpi_period)) \
                          .scalar() or 0
    prev_orders_kpi = db.session.query(func.count(Order.OrderID)) \
                          .filter(Order.OrderDate.between(start_prev_kpi_period, end_prev_kpi_period)) \
                          .scalar() or 0
    order_growth_val = None
    if prev_orders_kpi and prev_orders_kpi != 0:
        order_growth_val = ((curr_orders_kpi - prev_orders_kpi) / prev_orders_kpi) * 100
    order_growth_text = f"{round(order_growth_val, 2)}%" if order_growth_val is not None else '—'
    order_growth_class = get_growth_class(order_growth_val)

    curr_sales_kpi = db.session.query(func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), 0)) \
                         .join(Order, Order.OrderID == OrderItem.OrderID) \
                         .filter(Order.OrderDate.between(start_current_kpi_period, end_current_kpi_period)) \
                         .scalar() or 0
    prev_sales_kpi = db.session.query(func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), 0)) \
                         .join(Order, Order.OrderID == OrderItem.OrderID) \
                         .filter(Order.OrderDate.between(start_prev_kpi_period, end_prev_kpi_period)) \
                         .scalar() or 0
    sales_growth_val = None
    if prev_sales_kpi and prev_sales_kpi != 0:
        sales_growth_val = ((curr_sales_kpi - prev_sales_kpi) / prev_sales_kpi) * 100
    sales_growth_text = f"{round(sales_growth_val, 2)}%" if sales_growth_val is not None else '—'
    sales_growth_class = get_growth_class(sales_growth_val)
    total_orders_all_time = db.session.query(func.count(Order.OrderID)).scalar() or 0

    # --- Recent Supplies Table ---
    supplies_raw = (
        db.session.query(
            SupplyContract.SupplyID, SupplyContract.CreatedDate, SupplyContract.ContractPrice,
            SupplyContract.SupplierID, SupplyStatus.StatusName, SupplyStatus.CssClassName
        )
        .join(SupplyStatus, SupplyStatus.SupplyStatusID == SupplyContract.SupplyStatusID)
        .order_by(SupplyContract.CreatedDate.desc()).limit(7).all()
    )
    supplies_table_data = []
    for s_item in supplies_raw:
        prev_contract_query = db.session.query(SupplyContract.ContractPrice).filter(
            SupplyContract.SupplierID == s_item.SupplierID,
            SupplyContract.CreatedDate < s_item.CreatedDate
        ).order_by(SupplyContract.CreatedDate.desc()).first()
        prev_price = prev_contract_query[0] if prev_contract_query and prev_contract_query[0] is not None else None
        current_price = s_item.ContractPrice if s_item.ContractPrice is not None else 0
        price_change_val = None
        if prev_price is not None and prev_price != 0:
            price_change_val = ((current_price - prev_price) / prev_price) * 100
        elif prev_price is None and current_price != 0 and \
                not db.session.query(SupplyContract.SupplyID).filter(
                    SupplyContract.SupplierID == s_item.SupplierID,
                    SupplyContract.CreatedDate < s_item.CreatedDate).first():
            price_change_val = None
        supplies_table_data.append({
            'id': s_item.SupplyID, 'date': s_item.CreatedDate.strftime('%d-%m-%Y'),
            'status': s_item.StatusName,
            'status_class': s_item.CssClassName if s_item.CssClassName else "status-default",
            'change_text': f"{round(price_change_val, 2)}%" if price_change_val is not None else '—',
            'change_class': get_growth_class(price_change_val)
        })

    # --- Zone Occupancy Table ---
    zones_table_data = []
    try:
        zone_stats_raw = (
            db.session.query(
                Zone.ZoneCode.label('zone_code'),
                ZoneOccupancyView.TotalLocations.label('total_loc'),
                ZoneOccupancyView.OccupiedLocations.label('occ_loc'),
                ZoneOccupancyView.OccupancyPercentage.label('pct')
            )
            .join(Zone, Zone.ZoneID == ZoneOccupancyView.ZoneID)
            .order_by(Zone.ZoneCode).limit(7).all()
        )
        for z_item in zone_stats_raw:
            zones_table_data.append({
                'zone': z_item.zone_code,
                'total_locations': z_item.total_loc or 0,
                'occupied_locations': z_item.occ_loc or 0,
                'used_pct_val': z_item.pct if z_item.pct is not None else 0.0,
                'used_pct_text': f"{z_item.pct:.2f}%" if z_item.pct is not None else "0.00%"
            })
    except Exception as e:
        current_app.logger.error(f"Error fetching zone occupancy: {e}")
        print(f"Error fetching zone occupancy: {e}")
        pass

    # --- Initial Chart Data for page load ---
    query_initial_chart = db.session.query(
        Order.OrderDate,
        func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), 0).label('daily_sales_sum'),
        func.coalesce(func.sum(OrderItem.Quantity), 0).label('daily_quantity_sum')
    ).join(OrderItem, Order.OrderID == OrderItem.OrderID) \
        .join(Product, Product.ProductID == OrderItem.ProductID) \
        .filter(Order.OrderDate.between(initial_start_date, initial_end_date))

    if selected_category_id_chart_form:
        query_initial_chart = query_initial_chart.filter(Product.ProductCategoryID == selected_category_id_chart_form)
    if selected_manufacturer_id_chart_form:
        query_initial_chart = query_initial_chart.filter(Product.ManufacturerID == selected_manufacturer_id_chart_form)

    initial_sales_raw = query_initial_chart.group_by(Order.OrderDate).order_by(Order.OrderDate).all()

    chart_labels_initial = []
    chart_sales_values_initial = []
    chart_quantity_values_initial = []
    data_map_initial = {row.OrderDate: (float(row.daily_sales_sum), int(row.daily_quantity_sum)) for row in
                        initial_sales_raw}

    current_day_initial = initial_start_date
    while current_day_initial <= initial_end_date:
        chart_labels_initial.append(current_day_initial.strftime('%d-%m'))
        sales_val, qty_val = data_map_initial.get(current_day_initial, (0.0, 0))
        chart_sales_values_initial.append(sales_val)
        chart_quantity_values_initial.append(qty_val)
        current_day_initial += timedelta(days=1)

    # --- Top Cities Table ---
    end_date_top_cities_current_year = today_dt
    start_date_top_cities_current_year = end_date_top_cities_current_year - relativedelta(years=1) + timedelta(days=1)
    end_date_top_cities_previous_year = start_date_top_cities_current_year - timedelta(days=1)
    start_date_top_cities_previous_year = end_date_top_cities_previous_year - relativedelta(years=1) + timedelta(days=1)

    current_year_cities_data = (
        db.session.query(City.CityName, func.count(Order.OrderID).label('cnt'))
        .join(Order, Order.CityID == City.CityID)
        .filter(Order.OrderDate.between(start_date_top_cities_current_year, end_date_top_cities_current_year))
        .group_by(City.CityName).order_by(desc('cnt')).limit(10).all()
    )
    previous_year_cities_data = (
        db.session.query(City.CityName, func.count(Order.OrderID).label('cnt'))
        .join(Order, Order.CityID == City.CityID)
        .filter(Order.OrderDate.between(start_date_top_cities_previous_year, end_date_top_cities_previous_year))
        .group_by(City.CityName).all()
    )
    prev_map_top_cities = {name: cnt for name, cnt in previous_year_cities_data}
    top_cities_table_data = []
    for name, cnt_val in current_year_cities_data:
        prev_cnt = prev_map_top_cities.get(name, 0)
        city_change_val = None
        change_text_for_city = "—"
        if prev_cnt is not None and prev_cnt != 0:
            city_change_val = ((cnt_val - prev_cnt) / prev_cnt) * 100
            change_text_for_city = f"{round(city_change_val, 2)}%"
        elif prev_cnt == 0 and cnt_val == 0:
            city_change_val = 0
        top_cities_table_data.append({
            'city': name, 'cnt': cnt_val,
            'change_text': change_text_for_city,
            'change_class': get_growth_class(city_change_val)
        })

    return render_template('index.html',
                           curr_orders_kpi=curr_orders_kpi,
                           order_growth_text=order_growth_text,
                           order_growth_class=order_growth_class,
                           curr_sales_kpi=f"{curr_sales_kpi:,.2f}".replace(",", " "),
                           sales_growth_text=sales_growth_text,
                           sales_growth_class=sales_growth_class,
                           total_orders_all_time=total_orders_all_time,
                           supplies_table_data=supplies_table_data,
                           zones_table_data=zones_table_data,
                           chart_labels=chart_labels_initial,  # початкові дані
                           chart_sales_values=chart_sales_values_initial,
                           chart_quantity_values=chart_quantity_values_initial,
                           start_date_chart_form=initial_start_date.strftime('%Y-%m-%d'),
                           end_date_chart_form=initial_end_date.strftime('%Y-%m-%d'),
                           categories_filter_data=categories_filter_data,
                           selected_category_id_chart_form=selected_category_id_chart_form,
                           manufacturers_filter_data=manufacturers_filter_data,
                           selected_manufacturer_id_chart_form=selected_manufacturer_id_chart_form,
                           top_cities_table_data=top_cities_table_data,
                           default_start_date_chart_str=default_start_date_chart.strftime('%Y-%m-%d'),
                           default_end_date_chart_str=default_end_date_chart.strftime('%Y-%m-%d')
                           )