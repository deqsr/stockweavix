from flask import Blueprint, render_template, request, url_for, flash, redirect, jsonify
from app.models import db, Inventory, Product, ProductCategory, Manufacturer, Location, ZoneRow, Zone, ZoneSection, \
    Warehouse, ZoneShelf
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import or_, and_
from datetime import datetime, timezone

inv_bp = Blueprint('inv_bp', __name__)


@inv_bp.route('/')
def inventory_list():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    search_term = request.args.get('search', '').strip()
    cat_id_str = request.args.get('category_id', '')
    mfg_id_str = request.args.get('manufacturer_id', '')

    cat_id = int(cat_id_str) if cat_id_str.isdigit() else None
    mfg_id = int(mfg_id_str) if mfg_id_str.isdigit() else None

    all_categories_for_filter = ProductCategory.query.order_by(ProductCategory.CategoryName).all()
    all_manufacturers_for_filter = Manufacturer.query.order_by(Manufacturer.ManufacturerName).all()

    query = Inventory.query.options(
        joinedload(Inventory.product).joinedload(Product.category),
        joinedload(Inventory.product).joinedload(Product.manufacturer),
        joinedload(Inventory.location).joinedload(Location.row).joinedload(ZoneRow.zone),
        joinedload(Inventory.location).joinedload(Location.section),
        joinedload(Inventory.location).joinedload(Location.shelf),
        joinedload(Inventory.location).joinedload(Location.warehouse)
    ).join(Product, Inventory.ProductID == Product.ProductID)

    filter_conditions = []
    if cat_id:
        filter_conditions.append(Product.ProductCategoryID == cat_id)

    if mfg_id:
        filter_conditions.append(Product.ManufacturerID == mfg_id)

    if filter_conditions:
        query = query.filter(and_(*filter_conditions))

    if search_term:
        search_or_conditions = [
            Product.SKU.ilike(f"%{search_term}%"),
            Product.ProductName.ilike(f"%{search_term}%")
        ]
        try:
            loc_id_search = int(search_term)
            search_or_conditions.append(Inventory.LocationID == loc_id_search)
        except ValueError:
            pass

        query = query.filter(or_(*search_or_conditions))

    query = query.order_by(Product.ProductName)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'inventory/inventory_list.html',
        pagination=pagination,
        all_categories_for_filter=all_categories_for_filter,
        selected_category_id=cat_id,
        all_manufacturers_for_filter=all_manufacturers_for_filter,
        selected_manufacturer_id=mfg_id,
        search_term=search_term
    )


@inv_bp.route('/new', methods=['GET', 'POST'])
def create_inventory_item():
    form_data = request.form if request.method == 'POST' else {}
    all_products_for_form = Product.query.order_by(Product.ProductName).all()

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        location_id = request.form.get('location_id', type=int)
        quantity = request.form.get('quantity', type=int)

        if not product_id or not location_id or quantity is None:
            flash('Товар, фінальна локація та кількість є обов\'язковими полями.', 'warning')
            return render_template('inventory/create_inventory_item_form.html',
                                   all_products=all_products_for_form,
                                   form_data=form_data), 400

        if quantity <= 0:
            flash('Кількість повинна бути більше нуля.', 'warning')
            return render_template('inventory/create_inventory_item_form.html',
                                   all_products=all_products_for_form,
                                   form_data=form_data), 400

        existing_item = Inventory.query.filter_by(ProductID=product_id, LocationID=location_id).first()

        if existing_item:
            product = Product.query.get(product_id)
            location = Location.query.get(location_id)
            flash(
                f'Запис для товару "{product.ProductName if product else "N/A"}" на локації "{location.full_address() if location else "N/A"}" вже існує. Будь ласка, редагуйте існуючий запис (ID: {existing_item.InventoryID}).',
                'info')
            return redirect(url_for('inv_bp.edit_inventory_item', inventory_id=existing_item.InventoryID))

        new_inventory_item = Inventory(
            ProductID=product_id,
            LocationID=location_id,
            Quantity=quantity,
            LastUpdated=datetime.now(timezone.utc)
        )
        db.session.add(new_inventory_item)
        try:
            db.session.commit()
            flash(f'Новий запис на складі (ID: {new_inventory_item.InventoryID}) успішно створено.', 'success')
            return redirect(url_for('inv_bp.view_inventory_item', inventory_id=new_inventory_item.InventoryID))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при створенні запису: {str(e)}', 'danger')
            return render_template('inventory/create_inventory_item_form.html',
                                   all_products=all_products_for_form,
                                   form_data=request.form)

    return render_template('inventory/create_inventory_item_form.html',
                           all_products=all_products_for_form,
                           form_data=form_data)


@inv_bp.route('/<int:inventory_id>/view')
def view_inventory_item(inventory_id):
    item = Inventory.query.options(
        joinedload(Inventory.product).joinedload(Product.category),
        joinedload(Inventory.product).joinedload(Product.manufacturer),
        joinedload(Inventory.location).joinedload(Location.warehouse),
        joinedload(Inventory.location).joinedload(Location.row).joinedload(ZoneRow.zone),
        joinedload(Inventory.location).joinedload(Location.section),
        joinedload(Inventory.location).joinedload(Location.shelf)
    ).get_or_404(inventory_id)
    return render_template('inventory/inventory_item_details_view.html', item=item)


@inv_bp.route('/<int:inventory_id>/edit', methods=['GET', 'POST'])
def edit_inventory_item(inventory_id):
    inventory_item_to_edit = Inventory.query.options(
        joinedload(Inventory.product),
        joinedload(Inventory.location).joinedload(Location.warehouse),
        joinedload(Inventory.location).joinedload(Location.row).joinedload(ZoneRow.zone),
        joinedload(Inventory.location).joinedload(Location.section),
        joinedload(Inventory.location).joinedload(Location.shelf)
    ).get_or_404(inventory_id)

    form_data_from_req = request.form if request.method == 'POST' else {}

    if request.method == 'POST':
        location_id_form = request.form.get('location_id', type=int)
        quantity_form = request.form.get('quantity', type=int)

        if location_id_form is None or quantity_form is None:
            flash('Фінальна локація та кількість є обов\'язковими для оновлення.', 'warning')
            return render_template('inventory/edit_inventory_item_form.html',
                                   inventory_item=inventory_item_to_edit,
                                   form_data=form_data_from_req), 400

        if quantity_form < 0:
            flash('Кількість не може бути від\'ємною.', 'warning')
            return render_template('inventory/edit_inventory_item_form.html',
                                   inventory_item=inventory_item_to_edit,
                                   form_data=form_data_from_req), 400

        if inventory_item_to_edit.LocationID != location_id_form:
            conflicting_item = Inventory.query.filter(
                Inventory.ProductID == inventory_item_to_edit.ProductID,
                Inventory.LocationID == location_id_form,
                Inventory.InventoryID != inventory_item_to_edit.InventoryID
            ).first()
            if conflicting_item:
                product = Product.query.get(inventory_item_to_edit.ProductID)
                flash(
                    f'Неможливо змінити локацію. Товар "{product.ProductName if product else "N/A"}" вже існує на вибраній новій локації (ID запису: {conflicting_item.InventoryID}). Видаліть або об\'єднайте записи.',
                    'danger')
                return render_template('inventory/edit_inventory_item_form.html',
                                       inventory_item=inventory_item_to_edit,
                                       form_data=request.form)

        inventory_item_to_edit.LocationID = location_id_form
        inventory_item_to_edit.Quantity = quantity_form
        inventory_item_to_edit.LastUpdated = datetime.now(timezone.utc)

        try:
            db.session.commit()
            flash(f'Запис на складі ID {inventory_item_to_edit.InventoryID} успішно оновлено.', 'success')
            return redirect(url_for('inv_bp.view_inventory_item', inventory_id=inventory_item_to_edit.InventoryID))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при оновленні запису: {str(e)}', 'danger')
            return render_template('inventory/edit_inventory_item_form.html',
                                   inventory_item=inventory_item_to_edit,
                                   form_data=request.form)

    form_data_for_get = {
        'quantity': inventory_item_to_edit.Quantity
    }
    return render_template('inventory/edit_inventory_item_form.html',
                           inventory_item=inventory_item_to_edit,
                           form_data=form_data_for_get)


@inv_bp.route('/api/warehouses')
def api_get_warehouses():
    warehouses = Warehouse.query.order_by(Warehouse.WarehouseName).all()
    return jsonify([{'WarehouseID': w.WarehouseID, 'WarehouseName': w.WarehouseName} for w in warehouses])


@inv_bp.route('/api/zones')
def api_get_zones():
    warehouse_id = request.args.get('warehouse_id', type=int)
    if not warehouse_id:
        return jsonify([])
    zones = Zone.query.filter_by(WarehouseID=warehouse_id).order_by(Zone.ZoneCode).all()
    return jsonify([{'ZoneID': z.ZoneID, 'ZoneName': z.ZoneName} for z in zones])


@inv_bp.route('/api/rows')
def api_get_rows():
    zone_id = request.args.get('zone_id', type=int)
    if not zone_id:
        return jsonify([])
    rows = ZoneRow.query.filter_by(ZoneID=zone_id).order_by(ZoneRow.RowNumber).all()
    return jsonify([{'ZoneRowID': r.ZoneRowID, 'RowNumber': str(r.RowNumber)} for r in rows])


@inv_bp.route('/api/sections')
def api_get_sections():
    row_id = request.args.get('row_id', type=int)
    if not row_id:
        return jsonify([])

    distinct_section_ids = db.session.query(Location.SectionID) \
        .filter(Location.ZoneRowID == row_id, Location.SectionID.isnot(None)) \
        .distinct().all()

    section_ids = [sid[0] for sid in distinct_section_ids if sid[0] is not None]
    if not section_ids:
        return jsonify([])

    sections = ZoneSection.query.filter(ZoneSection.SectionID.in_(section_ids)).order_by(
        ZoneSection.SectionNumber).all()
    return jsonify([{'SectionID': s.SectionID, 'SectionNumber': str(s.SectionNumber)} for s in sections])


@inv_bp.route('/api/shelves')
def api_get_shelves():
    row_id = request.args.get('row_id', type=int)
    section_id = request.args.get('section_id', type=int)

    query = db.session.query(Location.ShelfID).distinct()
    filters = [Location.ShelfID.isnot(None)]

    if section_id:
        filters.append(Location.SectionID == section_id)
        if row_id:
            filters.append(Location.ZoneRowID == row_id)
    elif row_id:
        filters.append(Location.ZoneRowID == row_id)
    else:
        return jsonify([])

    distinct_shelf_ids_tuples = query.filter(and_(*filters)).all()
    shelf_ids = [sid[0] for sid in distinct_shelf_ids_tuples if sid[0] is not None]

    if not shelf_ids:
        return jsonify([])

    shelves = ZoneShelf.query.filter(ZoneShelf.ShelfID.in_(shelf_ids)).order_by(ZoneShelf.ShelfLevel).all()
    return jsonify([{'ShelfID': s.ShelfID, 'ShelfLevel': str(s.ShelfLevel)} for s in shelves])


@inv_bp.route('/api/locations/filter')
def api_filter_locations():
    warehouse_id = request.args.get('warehouse_id', type=int)
    zone_id = request.args.get('zone_id', type=int)
    row_id = request.args.get('row_id', type=int)
    section_id = request.args.get('section_id', type=int)
    shelf_id = request.args.get('shelf_id', type=int)

    query = Location.query.options(
        joinedload(Location.warehouse),
        joinedload(Location.row).joinedload(ZoneRow.zone),
        joinedload(Location.section),
        joinedload(Location.shelf)
    )

    filters = []
    if warehouse_id:
        filters.append(Location.WarehouseID == warehouse_id)
    else:
        return jsonify([])

    if zone_id:
        query = query.join(ZoneRow, Location.ZoneRowID == ZoneRow.ZoneRowID, isouter=False)
        filters.append(ZoneRow.ZoneID == zone_id)

    if row_id:
        filters.append(Location.ZoneRowID == row_id)

    if section_id:
        filters.append(Location.SectionID == section_id)
    else:
        pass

    if shelf_id:
        filters.append(Location.ShelfID == shelf_id)
    else:
        pass

    if filters:
        query = query.filter(and_(*filters))

    query = query.order_by(Location.LocationID)

    locations = query.limit(200).all()

    return jsonify([
        {'LocationID': loc.LocationID, 'full_address': loc.full_address()}
        for loc in locations
    ])