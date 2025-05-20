from flask import Blueprint, render_template
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from app.models import (
    db,
    Order,
    OrderItem,
    SupplyContracts,
    City,
    Zone,
    ZoneOccupancyView
)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    today = datetime.utcnow().date()

    # 1) Періоди для KPI: поточний і попередній місяць
    start_current = today - relativedelta(months=1)
    start_prev    = start_current - relativedelta(months=1)
    end_prev      = start_current

    # 2) Нові замовлення і ріст
    curr_orders = db.session.query(func.count(Order.OrderID)) \
        .filter(Order.OrderDate >= start_current) \
        .scalar() or 0
    prev_orders = db.session.query(func.count(Order.OrderID)) \
        .filter(Order.OrderDate >= start_prev,
                Order.OrderDate < end_prev) \
        .scalar() or 0
    order_growth = (curr_orders - prev_orders) / prev_orders * 100 if prev_orders else None

    # 3) Продажі за місяць і ріст
    curr_sales = db.session.query(
        func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), 0)
    ) \
    .join(Order, Order.OrderID == OrderItem.OrderID) \
    .filter(Order.OrderDate >= start_current) \
    .scalar() or 0
    prev_sales = db.session.query(
        func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), 0)
    ) \
    .join(Order, Order.OrderID == OrderItem.OrderID) \
    .filter(Order.OrderDate >= start_prev,
            Order.OrderDate < end_prev) \
    .scalar() or 0
    sales_growth = (curr_sales - prev_sales) / prev_sales * 100 if prev_sales else None

    # 4) Загальна кількість замовлень
    total_orders = db.session.query(func.count(Order.OrderID)).scalar() or 0

    # 5) Останні 7 поставок із Δ%
    supplies_raw = (
        db.session.query(
            SupplyContracts.SupplyID,
            SupplyContracts.CreatedDate,
            SupplyContracts.ContractPrice,
            SupplyContracts.SupplierID
        )
        .order_by(SupplyContracts.CreatedDate.desc())
        .limit(7)
        .all()
    )
    supplies = []
    for s in supplies_raw:
        status = SupplyContracts.query.get(s.SupplyID).status.StatusName
        prev = (
            db.session.query(SupplyContracts.ContractPrice)
            .filter(
                SupplyContracts.SupplierID == s.SupplierID,
                SupplyContracts.SupplyID < s.SupplyID
            )
            .order_by(SupplyContracts.SupplyID.desc())
            .first()
        )
        prev_price = prev[0] if prev else None
        pct = round((s.ContractPrice - prev_price) / prev_price * 100) if prev_price else None
        supplies.append({
            'id':     s.SupplyID,
            'date':   s.CreatedDate.strftime('%d-%m-%Y'),
            'status': status,
            'change': f"{pct}%" if pct is not None else '—'
        })

    # 6) Завантаженість зон (до 7) через ZoneOccupancyView + Zone.ZoneCode
    zone_stats = (
        db.session.query(
            Zone.ZoneCode.label('zone'),
            ZoneOccupancyView.TotalLocations.label('total_loc'),
            ZoneOccupancyView.OccupiedLocations.label('occ_loc'),
            ZoneOccupancyView.OccupancyPercentage.label('pct')
        )
        .join(Zone, Zone.ZoneID == ZoneOccupancyView.ZoneID)
        .order_by(Zone.ZoneCode)
        .limit(7)
        .all()
    )
    zones = []
    for z in zone_stats:
        zones.append({
            'zone':     z.zone,
            'status':   f"{z.occ_loc} / {z.total_loc}",
            'quantity': z.occ_loc,
            'used_pct': f"{z.pct:.2f}%"
        })

    # 7) Дані для графіка продажів за останні 30 днів
    start_30 = today - timedelta(days=30)
    sales_by_day = (
        db.session.query(
            Order.OrderDate,
            func.coalesce(func.sum(OrderItem.UnitPrice * OrderItem.Quantity), 0)
                .label('daily_sum')
        )
        .join(OrderItem, Order.OrderID == OrderItem.OrderID)
        .filter(Order.OrderDate >= start_30)
        .group_by(Order.OrderDate)
        .order_by(Order.OrderDate)
        .all()
    )
    chart_labels = [row.OrderDate.strftime('%d-%m') for row in sales_by_day]
    chart_values = [float(row.daily_sum) for row in sales_by_day]

    # 8) Топ-5 міст за рік з Δ%
    one_year = today - relativedelta(years=1)
    curr_city = (
        db.session.query(City.CityName, func.count(Order.OrderID).label('cnt'))
        .join(Order, Order.CityID == City.CityID)
        .filter(Order.OrderDate >= one_year)
        .group_by(City.CityName)
        .order_by(desc('cnt'))
        .limit(10)
        .all()
    )
    prev_city = (
        db.session.query(City.CityName, func.count(Order.OrderID).label('cnt'))
        .join(Order, Order.CityID == City.CityID)
        .filter(Order.OrderDate >= one_year - relativedelta(years=1),
                Order.OrderDate < one_year)
        .group_by(City.CityName)
        .all()
    )
    prev_map = {name: cnt for name, cnt in prev_city}
    top_cities = []
    for name, cnt in curr_city:
        prev_cnt = prev_map.get(name, 0)
        pct = round((cnt - prev_cnt) / prev_cnt * 100) if prev_cnt else None
        top_cities.append({
            'city': name,
            'cnt': cnt,
            'change': f"{pct}%" if pct is not None else '—'
        })

    return render_template('index.html',
                           new_orders=curr_orders,
                           order_growth=f"{round(order_growth)}%" if order_growth is not None else '—',
                           total_sales=round(curr_sales, 2),
                           sales_growth=f"{round(sales_growth)}%" if sales_growth is not None else '—',
                           total_orders=total_orders,
                           supplies=supplies,
                           zones=zones,
                           chart_labels=chart_labels,
                           chart_values=chart_values,
                           top_cities=top_cities
                           )