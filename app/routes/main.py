# app/routes/main.py
from flask import Blueprint, render_template, current_app, request, jsonify
from sqlalchemy import func, desc, cast, Date as SQLDate, text
from app.models import (
    db, Order, OrderItem, Product, ProductCategory, Manufacturer,
    SupplyContract, SupplyStatus, City, Zone, ZoneOccupancyView
)
from datetime import datetime, timedelta, date as py_date
from dateutil.relativedelta import relativedelta
import decimal
from flask_login import login_required

main_bp = Blueprint('main', __name__)


def get_growth_style(value):
    if value is None: return "text-growth-neutral"
    if value == 0: return "text-growth-neutral"
    if value > 0: return "text-growth-positive"
    return "text-growth-negative"


def get_chart_data_from_db(start_dt, end_dt, cat_id=None, mfg_id=None):
    if isinstance(start_dt, str):
        start_dt = datetime.strptime(start_dt, '%Y-%m-%d').date()
    if isinstance(end_dt, str):
        end_dt = datetime.strptime(end_dt, '%Y-%m-%d').date()

    group_by_date_sql = cast(Order.OrderDate, SQLDate)
    label_date_format = '%d-%m'

    query = db.session.query(
        group_by_date_sql.label('order_day'),
        func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), decimal.Decimal('0.0')).label('total_sales'),
        func.coalesce(func.sum(OrderItem.Quantity), 0).label('total_quantity')
    ).join(Order, Order.OrderID == OrderItem.OrderID) \
        .filter(Order.OrderDate.between(start_dt, end_dt))

    if cat_id and cat_id != 'all':
        query = query.join(Product, Product.ProductID == OrderItem.ProductID) \
            .filter(Product.ProductCategoryID == int(cat_id))
    if mfg_id and mfg_id != 'all':
        if not (cat_id and cat_id != 'all'):
            query = query.join(Product, Product.ProductID == OrderItem.ProductID)
        query = query.filter(Product.ManufacturerID == int(mfg_id))

    db_results = query.group_by(group_by_date_sql).order_by(group_by_date_sql).all()

    sales_map = {str(row.order_day): {'sales': float(row.total_sales), 'quantity': int(row.total_quantity)} for row in
                 db_results}

    chart_labels = []
    sales_on_chart = []
    quantity_on_chart = []

    current_day = start_dt
    while current_day <= end_dt:
        lookup_key_for_map = current_day.strftime('%Y-%m-%d')
        display_label = current_day.strftime(label_date_format)

        chart_labels.append(display_label)
        day_data = sales_map.get(lookup_key_for_map, {'sales': 0.0, 'quantity': 0})
        sales_on_chart.append(day_data['sales'])
        quantity_on_chart.append(day_data['quantity'])

        current_day += timedelta(days=1)

    return chart_labels, sales_on_chart, quantity_on_chart


@main_bp.route('/api/chart-data')
@login_required
def api_chart_data_endpoint():
    start_date_param = request.args.get('start_date')
    end_date_param = request.args.get('end_date')
    category_param = request.args.get('category_filter', 'all')
    manufacturer_param = request.args.get('manufacturer_filter', 'all')

    try:
        start_obj = datetime.strptime(start_date_param, '%Y-%m-%d').date()
        end_obj = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        if start_obj > end_obj:
            return jsonify({"error": "Start date cannot be after end date."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    labels, sales_values, quantity_values = get_chart_data_from_db(
        start_obj, end_obj, category_param, manufacturer_param
    )

    if not labels:
        return jsonify({
            "labels": [], "sales_values": [], "quantity_values": [],
            "message": "Немає даних за вибраний період та фільтрами."
        })

    return jsonify({
        "labels": labels,
        "sales_values": sales_values,
        "quantity_values": quantity_values
    })


@main_bp.route('/')
@login_required
def dashboard():
    today = py_date.today()

    default_chart_end_date = today
    default_chart_start_date = default_chart_end_date - timedelta(days=29)

    form_chart_start_date_str = request.args.get('start_date_chart', default_chart_start_date.strftime('%Y-%m-%d'))
    form_chart_end_date_str = request.args.get('end_date_chart', default_chart_end_date.strftime('%Y-%m-%d'))
    form_category_filter = request.args.get('category_filter', 'all')
    form_manufacturer_filter = request.args.get('manufacturer_filter', 'all')

    try:
        chart_query_start_date = datetime.strptime(form_chart_start_date_str, '%Y-%m-%d').date()
        chart_query_end_date = datetime.strptime(form_chart_end_date_str, '%Y-%m-%d').date()
        if chart_query_start_date > chart_query_end_date:
            chart_query_start_date = default_chart_start_date
            chart_query_end_date = default_chart_end_date
            form_chart_start_date_str = default_chart_start_date.strftime('%Y-%m-%d')
            form_chart_end_date_str = default_chart_end_date.strftime('%Y-%m-%d')
    except ValueError:
        chart_query_start_date = default_chart_start_date
        chart_query_end_date = default_chart_end_date
        form_chart_start_date_str = default_chart_start_date.strftime('%Y-%m-%d')
        form_chart_end_date_str = default_chart_end_date.strftime('%Y-%m-%d')

    all_categories = db.session.query(ProductCategory.CategoryID, ProductCategory.CategoryName).order_by(
        ProductCategory.CategoryName).all()
    all_manufacturers = db.session.query(Manufacturer.ManufacturerID, Manufacturer.ManufacturerName).order_by(
        Manufacturer.ManufacturerName).all()

    kpi_today = py_date.today()
    if kpi_today.day > 15:
        kpi_current_start = kpi_today.replace(day=1)
    else:
        kpi_current_start = (kpi_today.replace(day=1) - timedelta(days=1)).replace(day=1)
    kpi_current_end = (kpi_current_start + relativedelta(months=1)) - timedelta(days=1)
    kpi_previous_start = kpi_current_start - relativedelta(months=1)
    kpi_previous_end = (kpi_previous_start + relativedelta(months=1)) - timedelta(days=1)

    kpi_orders_current = db.session.query(func.count(Order.OrderID)) \
                             .filter(Order.OrderDate.between(kpi_current_start, kpi_current_end)) \
                             .scalar() or 0
    kpi_orders_previous = db.session.query(func.count(Order.OrderID)) \
                              .filter(Order.OrderDate.between(kpi_previous_start, kpi_previous_end)) \
                              .scalar() or 0

    kpi_order_growth_value = None
    if kpi_orders_previous > 0:
        kpi_order_growth_value = ((kpi_orders_current - kpi_orders_previous) / kpi_orders_previous) * 100
    elif kpi_orders_current > 0 and kpi_orders_previous == 0:
        kpi_order_growth_value = float('inf')

    kpi_order_growth_display_text = f"{round(kpi_order_growth_value, 2)}%" if kpi_order_growth_value is not None and kpi_order_growth_value != float(
        'inf') else ('N/A' if kpi_order_growth_value == float('inf') else '—')
    kpi_order_growth_css_class = get_growth_style(
        kpi_order_growth_value if kpi_order_growth_value != float('inf') else 1)

    kpi_sales_current_decimal = db.session.query(
        func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), decimal.Decimal('0.0'))) \
                                    .join(Order, Order.OrderID == OrderItem.OrderID) \
                                    .filter(Order.OrderDate.between(kpi_current_start, kpi_current_end)) \
                                    .scalar() or decimal.Decimal('0.0')
    kpi_sales_previous_decimal = db.session.query(
        func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), decimal.Decimal('0.0'))) \
                                     .join(Order, Order.OrderID == OrderItem.OrderID) \
                                     .filter(Order.OrderDate.between(kpi_previous_start, kpi_previous_end)) \
                                     .scalar() or decimal.Decimal('0.0')

    kpi_sales_growth_value = None
    if kpi_sales_previous_decimal > 0:
        kpi_sales_growth_value = float(
            ((kpi_sales_current_decimal - kpi_sales_previous_decimal) / kpi_sales_previous_decimal) * 100)
    elif kpi_sales_current_decimal > 0 and kpi_sales_previous_decimal == 0:
        kpi_sales_growth_value = float('inf')

    kpi_sales_growth_display_text = f"{round(kpi_sales_growth_value, 2)}%" if kpi_sales_growth_value is not None and kpi_sales_growth_value != float(
        'inf') else ('N/A' if kpi_sales_growth_value == float('inf') else '—')
    kpi_sales_growth_css_class = get_growth_style(
        kpi_sales_growth_value if kpi_sales_growth_value != float('inf') else 1)

    total_orders_ever = db.session.query(func.count(Order.OrderID)).scalar() or 0

    recent_supplies_db = (
        db.session.query(
            SupplyContract.SupplyID, SupplyContract.CreatedDate, SupplyContract.ContractPrice,
            SupplyContract.SupplierID, SupplyStatus.StatusName, SupplyStatus.CssClassName
        )
        .join(SupplyStatus, SupplyStatus.SupplyStatusID == SupplyContract.SupplyStatusID)
        .order_by(SupplyContract.CreatedDate.desc()).limit(5).all()
    )
    supplies_for_table = [{
        'id': s.SupplyID,
        'date': s.CreatedDate.strftime('%d-%m-%Y'),
        'status': s.StatusName,
        'status_class': s.CssClassName or "status-default",
        'price': s.ContractPrice if s.ContractPrice is not None else decimal.Decimal('0.00')
    } for s in recent_supplies_db]

    zones_for_table = []
    try:
        zone_stats_from_db = (
            db.session.query(
                Zone.ZoneCode.label('zone_code'),
                ZoneOccupancyView.TotalLocations.label('total_spots'),
                ZoneOccupancyView.OccupiedLocations.label('occupied_spots'),
                ZoneOccupancyView.OccupancyPercentage.label('percent_used')
            )
            .join(Zone, Zone.ZoneID == ZoneOccupancyView.ZoneID)
            .order_by(Zone.ZoneCode).limit(5).all()
        )
        for item in zone_stats_from_db:
            zones_for_table.append({
                'zone_name': item.zone_code,
                'total_locations': item.total_spots or 0,
                'occupied_locations': item.occupied_spots or 0,
                'usage_percent_value': float(item.percent_used) if item.percent_used is not None else 0.0,
                'usage_percent_text': f"{float(item.percent_used):.2f}%" if item.percent_used is not None else "0.00%"
            })
    except Exception as e:
        current_app.logger.error(f"Error fetching zone occupancy: {e}")

    initial_chart_labels, initial_chart_sales, initial_chart_quantity = get_chart_data_from_db(
        chart_query_start_date, chart_query_end_date,
        form_category_filter, form_manufacturer_filter
    )
    chart_no_data_msg = "Немає даних за вибраний період та фільтрами." if not initial_chart_labels else None

    top_cities_end_current_year = today
    top_cities_start_current_year = top_cities_end_current_year - relativedelta(years=1) + timedelta(days=1)
    top_cities_end_previous_year = top_cities_start_current_year - timedelta(days=1)
    top_cities_start_previous_year = top_cities_end_previous_year - relativedelta(years=1) + timedelta(days=1)

    cities_current_year_data = (
        db.session.query(City.CityName, func.count(Order.OrderID).label('order_count'))
        .join(Order, Order.CityID == City.CityID)
        .filter(Order.OrderDate.between(top_cities_start_current_year, top_cities_end_current_year))
        .group_by(City.CityName).order_by(desc('order_count')).limit(10).all()
    )
    cities_previous_year_raw_data = (
        db.session.query(City.CityName, func.count(Order.OrderID).label('order_count'))
        .join(Order, Order.CityID == City.CityID)
        .filter(Order.OrderDate.between(top_cities_start_previous_year, top_cities_end_previous_year))
        .group_by(City.CityName).all()
    )
    cities_previous_year_map = {name: count for name, count in cities_previous_year_raw_data}

    top_cities_for_table = []
    for city_name, current_year_count in cities_current_year_data:
        previous_year_count = cities_previous_year_map.get(city_name, 0)
        city_growth_value = None
        city_growth_display_text = "—"

        if previous_year_count > 0:
            city_growth_value = ((current_year_count - previous_year_count) / previous_year_count) * 100
            city_growth_display_text = f"{round(city_growth_value, 2)}%"
        elif previous_year_count == 0 and current_year_count > 0:
            city_growth_display_text = "N/A"
            city_growth_value = float('inf')
        elif previous_year_count == 0 and current_year_count == 0:
            city_growth_value = 0
            city_growth_display_text = "0.00%"

        top_cities_for_table.append({
            'city_name': city_name,
            'order_count': current_year_count,
            'growth_text': city_growth_display_text,
            'growth_style': get_growth_style(
                city_growth_value if city_growth_value != float('inf') else 1
            )
        })

    return render_template('index.html',
                           kpi_orders_current=kpi_orders_current,
                           kpi_order_growth_text=kpi_order_growth_display_text,
                           kpi_order_growth_style=kpi_order_growth_css_class,
                           kpi_sales_current_display=f"{kpi_sales_current_decimal:,.2f}".replace(",", " "),
                           kpi_sales_growth_text=kpi_sales_growth_display_text,
                           kpi_sales_growth_style=kpi_sales_growth_css_class,
                           total_orders_ever=total_orders_ever,
                           supplies_for_table=supplies_for_table,
                           zones_for_table=zones_for_table,
                           top_cities_for_table=top_cities_for_table,

                           form_chart_start_val=form_chart_start_date_str,
                           form_chart_end_val=form_chart_end_date_str,
                           all_categories_for_filter=all_categories,
                           all_manufacturers_for_filter=all_manufacturers,
                           form_selected_category=form_category_filter,
                           form_selected_manufacturer=form_manufacturer_filter,

                           chart_initial_labels=initial_chart_labels,
                           chart_initial_sales_data=initial_chart_sales,
                           chart_initial_quantity_data=initial_chart_quantity,
                           chart_no_data_message=chart_no_data_msg
                           )