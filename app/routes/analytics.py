from flask import Blueprint, render_template, request
from sqlalchemy import func, cast, Date as SQLDate
from app.models import db, Order, OrderItem, Product, ProductCategory, Inventory
from datetime import datetime, timedelta, date as py_date
from dateutil.relativedelta import relativedelta
import pandas as pd

analytics_bp = Blueprint('analytics_bp', __name__)


def parse_date(date_str, default_date):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return default_date



def get_sales_dynamics_data(start_date_dt, end_date_dt, comparison_type):
    current_period_data = db.session.query(
        cast(Order.OrderDate, SQLDate).label('date'),
        func.coalesce(func.sum(OrderItem.Quantity * OrderItem.UnitPrice), 0).label('total_sales_sum'),
        func.coalesce(func.sum(OrderItem.Quantity), 0).label('total_quantity_sold'),
        func.count(func.distinct(Order.OrderID)).label('order_count')
    ).join(OrderItem, Order.OrderID == OrderItem.OrderID) \
        .filter(Order.OrderDate >= start_date_dt) \
        .filter(Order.OrderDate <= end_date_dt) \
        .group_by(cast(Order.OrderDate, SQLDate)) \
        .order_by(cast(Order.OrderDate, SQLDate)).all()

    comparison_period_data_list = []
    comp_start_date, comp_end_date = None, None

    if comparison_type == 'previous_period':
        period_duration_days = (end_date_dt - start_date_dt).days
        comp_end_date = start_date_dt - timedelta(days=1)
        comp_start_date = comp_end_date - timedelta(days=period_duration_days)
    elif comparison_type == 'previous_year':
        comp_start_date = start_date_dt - relativedelta(years=1)
        comp_end_date = end_date_dt - relativedelta(years=1)

    if comp_start_date and comp_end_date:
        comparison_period_data_raw = db.session.query(
            cast(Order.OrderDate, SQLDate).label('date'),
            func.coalesce(func.sum(OrderItem.Quantity * OrderItem.UnitPrice), 0).label('total_sales_sum')
        ).join(OrderItem, Order.OrderID == OrderItem.OrderID) \
            .filter(Order.OrderDate >= comp_start_date) \
            .filter(Order.OrderDate <= comp_end_date) \
            .group_by(cast(Order.OrderDate, SQLDate)) \
            .order_by(cast(Order.OrderDate, SQLDate)).all()

        for row in comparison_period_data_raw:
            original_date = row.date
            if comparison_type == 'previous_year':
                shifted_date = original_date + relativedelta(years=1)
            else:
                shifted_date = original_date + timedelta(days=(end_date_dt - start_date_dt).days + 1)
            comparison_period_data_list.append({'date': shifted_date, 'total_sales_sum': row.total_sales_sum})

    labels = []
    current_sales_sum_values = []
    current_quantity_sold_values = []
    current_order_count_values = []
    comparison_sales_sum_values = []

    delta = end_date_dt - start_date_dt
    all_dates = [start_date_dt + timedelta(days=i) for i in range(delta.days + 1)]

    current_data_map = {item.date: item for item in current_period_data}
    comparison_data_map = {item['date']: item for item in comparison_period_data_list}

    for dt in all_dates:
        labels.append(dt.strftime('%Y-%m-%d'))
        current_day_data = current_data_map.get(dt)
        current_sales_sum_values.append(float(current_day_data.total_sales_sum) if current_day_data else 0)
        current_quantity_sold_values.append(int(current_day_data.total_quantity_sold) if current_day_data else 0)
        current_order_count_values.append(int(current_day_data.order_count) if current_day_data else 0)

        comparison_day_data = comparison_data_map.get(dt)
        comparison_sales_sum_values.append(float(comparison_day_data['total_sales_sum']) if comparison_day_data else 0)

    return {
        'labels': labels,
        'current_sales_sum': current_sales_sum_values,
        'current_quantity_sold': current_quantity_sold_values,
        'current_order_count': current_order_count_values,
        'comparison_sales_sum': comparison_sales_sum_values if comparison_type != 'none' else [],
        'show_comparison': comparison_type != 'none'
    }


def get_abc_xyz_analysis_data(start_date_abc_xyz, end_date_abc_xyz):

    sales_data_query = db.session.query(
        Product.ProductID,
        Product.SKU,
        Product.ProductName,
        func.sum(OrderItem.Quantity * OrderItem.UnitPrice).label('total_revenue'),
    ).join(OrderItem, Product.ProductID == OrderItem.ProductID) \
        .join(Order, OrderItem.OrderID == Order.OrderID) \
        .filter(Order.OrderDate.between(start_date_abc_xyz, end_date_abc_xyz)) \
        .group_by(Product.ProductID, Product.SKU, Product.ProductName) \
        .having(func.sum(OrderItem.Quantity * OrderItem.UnitPrice) > 0) \
        .all()

    period_string = f"за період: {start_date_abc_xyz.strftime('%d.%m.%Y')} - {end_date_abc_xyz.strftime('%d.%m.%Y')}"
    if not sales_data_query:
        return {'table_data': [], 'abc_pie_data': {}, 'xyz_pie_data': {}, 'period_string': period_string}

    df_sales = pd.DataFrame([{
        'ProductID': p.ProductID, 'SKU': p.SKU, 'ProductName': p.ProductName,
        'total_revenue': float(p.total_revenue or 0)
    } for p in sales_data_query])

    df_sales = df_sales.sort_values(by='total_revenue', ascending=False)
    df_sales['revenue_cumulative_perc'] = (df_sales['total_revenue'].cumsum() / df_sales['total_revenue'].sum()) * 100

    def assign_abc_class(perc):
        if perc <= 70:
            return 'A'
        elif perc <= 90:
            return 'B'
        else:
            return 'C'

    df_sales['abc_class'] = df_sales['revenue_cumulative_perc'].apply(assign_abc_class)

    xyz_start_date = start_date_abc_xyz
    xyz_end_date = end_date_abc_xyz

    daily_sales_for_xyz_query = db.session.query(
        Product.ProductID,
        cast(Order.OrderDate, SQLDate).label('sale_date'),
        func.sum(OrderItem.Quantity).label('daily_quantity')
    ).join(OrderItem, Product.ProductID == OrderItem.ProductID) \
        .join(Order, OrderItem.OrderID == Order.OrderID) \
        .filter(Order.OrderDate.between(xyz_start_date, xyz_end_date)) \
        .filter(Product.ProductID.in_(df_sales['ProductID'].tolist())) \
        .group_by(Product.ProductID, cast(Order.OrderDate, SQLDate)) \
        .all()

    df_daily_sales_xyz = pd.DataFrame(daily_sales_for_xyz_query, columns=['ProductID', 'sale_date', 'daily_quantity'])

    xyz_classes = {}
    if not df_daily_sales_xyz.empty:
        all_dates_in_period = pd.date_range(start=xyz_start_date, end=xyz_end_date)

        for product_id in df_sales['ProductID']:
            product_daily_data = df_daily_sales_xyz[df_daily_sales_xyz['ProductID'] == product_id]

            product_sales_series = pd.Series(index=all_dates_in_period, dtype=float).fillna(0)
            if not product_daily_data.empty:
                for _, row in product_daily_data.iterrows():

                    sale_timestamp = pd.Timestamp(row['sale_date'])
                    if sale_timestamp in product_sales_series.index:
                        product_sales_series[sale_timestamp] = row['daily_quantity']

            std_dev = product_sales_series.std()
            mean_sales = product_sales_series.mean()

            if mean_sales > 0:
                cv = std_dev / mean_sales
                if cv <= 0.75:
                    xyz_classes[product_id] = 'X'
                elif cv <= 1.5:
                    xyz_classes[product_id] = 'Y'
                else:
                    xyz_classes[product_id] = 'Z'
            else:
                xyz_classes[product_id] = 'Z'
    else:

        for product_id in df_sales['ProductID']:
            xyz_classes[product_id] = 'Z'

    df_sales['xyz_class'] = df_sales['ProductID'].map(xyz_classes).fillna('Z')
    df_sales['abc_xyz_class'] = df_sales['abc_class'] + df_sales['xyz_class']

    table_data = df_sales[['SKU', 'ProductName', 'total_revenue', 'abc_class', 'xyz_class', 'abc_xyz_class']].to_dict(
        orient='records')
    for row in table_data:
        row['total_revenue'] = f"{row['total_revenue']:.2f}"

    abc_pie_data = df_sales['abc_class'].value_counts().to_dict()
    xyz_pie_data = df_sales['xyz_class'].value_counts().to_dict()

    return {'table_data': table_data, 'abc_pie_data': abc_pie_data, 'xyz_pie_data': xyz_pie_data,
            'period_string': period_string}


def get_inventory_turnover_data(start_date_turnover, end_date_turnover):

    results = []
    categories = ProductCategory.query.all()
    period_string_turnover = f"за період: {start_date_turnover.strftime('%d.%m.%Y')} - {end_date_turnover.strftime('%d.%m.%Y')}"

    for category in categories:
        current_stock_agg = db.session.query(func.sum(Inventory.Quantity)) \
            .join(Product).filter(Product.ProductCategoryID == category.CategoryID) \
            .scalar()
        current_stock = int(current_stock_agg or 0)

        sold_in_period_agg = db.session.query(func.sum(OrderItem.Quantity)) \
            .join(Product, OrderItem.ProductID == Product.ProductID) \
            .join(Order, OrderItem.OrderID == Order.OrderID) \
            .filter(Product.ProductCategoryID == category.CategoryID) \
            .filter(Order.OrderDate.between(start_date_turnover, end_date_turnover)) \
            .scalar()
        sold_in_period = int(sold_in_period_agg or 0)

        turnover_ratio = (sold_in_period / current_stock) if current_stock > 0 else 0

        results.append({
            'category_name': category.CategoryName,
            'current_stock': current_stock,
            'sold_in_period': sold_in_period,
            'turnover_ratio': f"{turnover_ratio:.2f}"
        })
    return {'data': sorted(results, key=lambda x: x['category_name']), 'period_string': period_string_turnover}


def get_dead_stock_data(days_threshold=90):

    if not isinstance(days_threshold, int) or days_threshold <= 0:
        days_threshold = 90
    cutoff_date = datetime.now().date() - timedelta(days=days_threshold)

    products_in_stock = db.session.query(
        Product.ProductID, Product.SKU, Product.ProductName,
        ProductCategory.CategoryName,
        Inventory.Quantity
    ).join(Inventory, Product.ProductID == Inventory.ProductID) \
        .join(ProductCategory, Product.ProductCategoryID == ProductCategory.CategoryID) \
        .filter(Inventory.Quantity > 0) \
        .all()

    dead_stock_items = []
    for p_stock in products_in_stock:
        last_sale = db.session.query(func.max(Order.OrderDate)) \
            .join(OrderItem, Order.OrderID == OrderItem.OrderID) \
            .filter(OrderItem.ProductID == p_stock.ProductID) \
            .scalar()

        if last_sale is None or last_sale < cutoff_date:
            dead_stock_items.append({
                'sku': p_stock.SKU,
                'product_name': p_stock.ProductName,
                'category_name': p_stock.CategoryName,
                'quantity': p_stock.Quantity,
                'last_sale_date': last_sale.strftime('%Y-%m-%d') if last_sale else f"> {days_threshold} днів"
            })
    return sorted(dead_stock_items, key=lambda x: x['product_name'])


def get_stock_out_forecast_data(sales_period_days=30):

    end_date_sales = datetime.now().date()
    start_date_sales = end_date_sales - timedelta(days=sales_period_days)

    products_in_stock = db.session.query(
        Product.ProductID, Product.SKU, Product.ProductName,
        ProductCategory.CategoryName,
        Inventory.Quantity
    ).join(Inventory, Product.ProductID == Inventory.ProductID) \
        .join(ProductCategory, Product.ProductCategoryID == ProductCategory.CategoryID) \
        .filter(Inventory.Quantity > 0) \
        .all()

    forecast_items = []
    for p_stock in products_in_stock:
        total_sold_in_period_agg = db.session.query(func.sum(OrderItem.Quantity)) \
            .join(Order, OrderItem.OrderID == Order.OrderID) \
            .filter(OrderItem.ProductID == p_stock.ProductID) \
            .filter(Order.OrderDate.between(start_date_sales, end_date_sales)) \
            .scalar()

        total_sold_in_period = int(total_sold_in_period_agg or 0)
        avg_daily_sales = (total_sold_in_period / sales_period_days) if sales_period_days > 0 else 0

        days_to_stock_out_str = "∞"
        if avg_daily_sales > 0:
            days_to_stock_out = p_stock.Quantity / avg_daily_sales
            days_to_stock_out_str = f"{days_to_stock_out:.1f}"

        forecast_items.append({
            'product_sku': f"{p_stock.ProductName} ({p_stock.SKU})",
            'category_name': p_stock.CategoryName,
            'current_stock': p_stock.Quantity,
            'avg_daily_sales': f"{avg_daily_sales:.2f}",
            'days_to_stock_out': days_to_stock_out_str
        })
    return sorted(forecast_items, key=lambda x: (
    float(x['days_to_stock_out']) if x['days_to_stock_out'] != "∞" else float('inf'), x['product_sku']))


@analytics_bp.route('/', methods=['GET'])
def analytics_dashboard():
    today = py_date.today()

    # Sales Dynamics
    default_start_date_dynamics_str = (today - timedelta(days=29)).strftime('%Y-%m-%d')  # 30 днів
    default_end_date_dynamics_str = today.strftime('%Y-%m-%d')
    start_date_dynamics_param = request.args.get('start_date_dynamics', default_start_date_dynamics_str)
    end_date_dynamics_param = request.args.get('end_date_dynamics', default_end_date_dynamics_str)
    comparison_type_param = request.args.get('comparison_type', 'none')
    start_date_dynamics_dt = parse_date(start_date_dynamics_param,
                                        datetime.strptime(default_start_date_dynamics_str, '%Y-%m-%d').date())
    end_date_dynamics_dt = parse_date(end_date_dynamics_param,
                                      datetime.strptime(default_end_date_dynamics_str, '%Y-%m-%d').date())
    if start_date_dynamics_dt > end_date_dynamics_dt:
        start_date_dynamics_dt = end_date_dynamics_dt - timedelta(days=29)
    sales_dynamics_chart_data = get_sales_dynamics_data(start_date_dynamics_dt, end_date_dynamics_dt,
                                                        comparison_type_param)

    # ABC/XYZ Analysis
    default_start_date_abc_xyz_str = (today - timedelta(days=89)).strftime('%Y-%m-%d')  # 90 днів за замовчуванням
    default_end_date_abc_xyz_str = today.strftime('%Y-%m-%d')
    start_date_abc_xyz_param = request.args.get('start_date_abc_xyz', default_start_date_abc_xyz_str)
    end_date_abc_xyz_param = request.args.get('end_date_abc_xyz', default_end_date_abc_xyz_str)
    start_date_abc_xyz_dt = parse_date(start_date_abc_xyz_param,
                                       datetime.strptime(default_start_date_abc_xyz_str, '%Y-%m-%d').date())
    end_date_abc_xyz_dt = parse_date(end_date_abc_xyz_param,
                                     datetime.strptime(default_end_date_abc_xyz_str, '%Y-%m-%d').date())
    if start_date_abc_xyz_dt > end_date_abc_xyz_dt:
        start_date_abc_xyz_dt = end_date_abc_xyz_dt - timedelta(days=89)  # Коригуємо, якщо дати не валідні
    abc_xyz_data = get_abc_xyz_analysis_data(start_date_abc_xyz_dt, end_date_abc_xyz_dt)

    # Inventory Turnover
    default_start_date_turnover_str = (today - timedelta(days=29)).strftime('%Y-%m-%d')  # 30 днів
    default_end_date_turnover_str = today.strftime('%Y-%m-%d')
    start_date_turnover_param = request.args.get('start_date_turnover', default_start_date_turnover_str)
    end_date_turnover_param = request.args.get('end_date_turnover', default_end_date_turnover_str)
    start_date_turnover_dt = parse_date(start_date_turnover_param,
                                        datetime.strptime(default_start_date_turnover_str, '%Y-%m-%d').date())
    end_date_turnover_dt = parse_date(end_date_turnover_param,
                                      datetime.strptime(default_end_date_turnover_str, '%Y-%m-%d').date())
    if start_date_turnover_dt > end_date_turnover_dt:
        start_date_turnover_dt = end_date_turnover_dt - timedelta(days=29)
    inventory_turnover_result = get_inventory_turnover_data(start_date_turnover_dt, end_date_turnover_dt)

    # Dead Stock
    default_dead_stock_days = 90
    dead_stock_days_param_str = request.args.get('dead_stock_days', str(default_dead_stock_days))
    try:
        dead_stock_days_param = int(dead_stock_days_param_str)
    except ValueError:
        dead_stock_days_param = default_dead_stock_days
    if dead_stock_days_param <= 0:
        dead_stock_days_param = default_dead_stock_days
    dead_stock_data = get_dead_stock_data(days_threshold=dead_stock_days_param)

    # Stock Out Forecast
    default_forecast_sales_days = 30
    forecast_sales_days_param_str = request.args.get('forecast_sales_days', str(default_forecast_sales_days))
    try:
        forecast_sales_days_param = int(forecast_sales_days_param_str)
    except ValueError:
        forecast_sales_days_param = default_forecast_sales_days
    if forecast_sales_days_param <= 0:
        forecast_sales_days_param = default_forecast_sales_days
    stock_out_forecast_data = get_stock_out_forecast_data(sales_period_days=forecast_sales_days_param)

    active_tab_target = request.args.get('active_tab_target', '#overview-pane')

    return render_template('analytics/dashboard.html',
                           sales_dynamics_chart_data=sales_dynamics_chart_data,
                           current_start_date_dynamics=start_date_dynamics_dt.strftime('%Y-%m-%d'),
                           current_end_date_dynamics=end_date_dynamics_dt.strftime('%Y-%m-%d'),
                           current_comparison_type=comparison_type_param,
                           default_start_date_dynamics_str=default_start_date_dynamics_str,
                           default_end_date_dynamics_str=default_end_date_dynamics_str,

                           abc_xyz_data=abc_xyz_data,
                           current_start_date_abc_xyz=start_date_abc_xyz_dt.strftime('%Y-%m-%d'),
                           current_end_date_abc_xyz=end_date_abc_xyz_dt.strftime('%Y-%m-%d'),
                           default_start_date_abc_xyz_str=default_start_date_abc_xyz_str,
                           default_end_date_abc_xyz_str=default_end_date_abc_xyz_str,

                           inventory_turnover_data=inventory_turnover_result['data'],
                           inventory_turnover_period_string=inventory_turnover_result['period_string'],
                           current_start_date_turnover=start_date_turnover_dt.strftime('%Y-%m-%d'),
                           current_end_date_turnover=end_date_turnover_dt.strftime('%Y-%m-%d'),
                           default_start_date_turnover_str=default_start_date_turnover_str,
                           default_end_date_turnover_str=default_end_date_turnover_str,

                           dead_stock_data=dead_stock_data,
                           current_dead_stock_days=dead_stock_days_param,
                           default_dead_stock_days=default_dead_stock_days,

                           stock_out_forecast_data=stock_out_forecast_data,
                           current_forecast_sales_days=forecast_sales_days_param,
                           default_forecast_sales_days=default_forecast_sales_days,

                           initial_active_tab=active_tab_target  # Передаємо активну вкладку в шаблон
                           )