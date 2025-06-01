from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import desc, or_, and_, text as sql_text
from app.models import db, Product, ProductCategory, Manufacturer
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone
import decimal

products_bp = Blueprint('products_bp', __name__, url_prefix='/products')


@products_bp.route('/')
def list_products():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    search_term = request.args.get('search', '').strip()
    category_id_filter_str = request.args.get('category_id', '')
    manufacturer_id_filter_str = request.args.get('manufacturer_id', '')

    category_id_filter = int(category_id_filter_str) if category_id_filter_str.isdigit() else None
    manufacturer_id_filter = int(manufacturer_id_filter_str) if manufacturer_id_filter_str.isdigit() else None

    query = Product.query.options(
        joinedload(Product.category),
        joinedload(Product.manufacturer)
    )

    filter_conditions = []

    if category_id_filter:
        filter_conditions.append(Product.ProductCategoryID == category_id_filter)
    if manufacturer_id_filter:
        filter_conditions.append(Product.ManufacturerID == manufacturer_id_filter)

    if search_term:
        search_or_conditions = [
            Product.ProductName.ilike(f"%{search_term}%"),
            Product.SKU.ilike(f"%{search_term}%"),
            Product.ProductDescription.ilike(f"%{search_term}%")
        ]

        try:
            product_id_search = int(search_term)
            search_or_conditions.append(Product.ProductID == product_id_search)
        except ValueError:
            pass

        filter_conditions.append(or_(*search_or_conditions))

    if filter_conditions:
        query = query.filter(and_(*filter_conditions))

    query = query.order_by(desc(Product.LastUpdated), Product.ProductName)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products_on_page = pagination.items

    all_categories = ProductCategory.query.order_by(ProductCategory.CategoryName).all()
    all_manufacturers = Manufacturer.query.order_by(Manufacturer.ManufacturerName).all()

    return render_template('products/products_list.html',
                           products=products_on_page,
                           pagination=pagination,
                           all_categories=all_categories,
                           selected_category_id=category_id_filter,
                           all_manufacturers=all_manufacturers,
                           selected_manufacturer_id=manufacturer_id_filter,
                           search_term=search_term)


@products_bp.route('/new', methods=['GET', 'POST'])
def create_product():
    form_data = request.form if request.method == 'POST' else {}
    all_categories = ProductCategory.query.order_by(ProductCategory.CategoryName).all()
    all_manufacturers = Manufacturer.query.order_by(Manufacturer.ManufacturerName).all()

    if request.method == 'POST':
        product_name = request.form.get('product_name', '').strip()
        category_id_str = request.form.get('category_id')
        manufacturer_id_str = request.form.get('manufacturer_id')
        price_str = request.form.get('price', '').replace(',', '.') # Changed default to empty string for optional price
        description = request.form.get('description', '').strip()

        if not product_name or not category_id_str:
            flash('Назва товару та категорія є обов\'язковими полями.', 'warning')
            return render_template('products/create_product_form.html',
                                   all_categories=all_categories,
                                   all_manufacturers=all_manufacturers,
                                   form_data=form_data), 400
        try:
            category_id = int(category_id_str)
        except ValueError:
            flash('Некоректне значення для категорії.', 'warning')
            return render_template('products/create_product_form.html',
                                   all_categories=all_categories,
                                   all_manufacturers=all_manufacturers,
                                   form_data=form_data), 400

        manufacturer_id = None
        if manufacturer_id_str and manufacturer_id_str.isdigit():
            manufacturer_id = int(manufacturer_id_str)

        price = None
        if price_str: # Only attempt conversion if price_str is not empty
            try:
                price_val = decimal.Decimal(price_str)
                if price_val >= 0:
                    price = price_val
                else:
                    flash('Ціна не може бути від\'ємною.', 'warning')
                    return render_template('products/create_product_form.html',
                                           all_categories=all_categories,
                                           all_manufacturers=all_manufacturers,
                                           form_data=form_data), 400
            except decimal.InvalidOperation:
                flash('Некоректний формат ціни.', 'warning')
                return render_template('products/create_product_form.html',
                                       all_categories=all_categories,
                                       all_manufacturers=all_manufacturers,
                                       form_data=form_data), 400

        # --- SKU Generation ---
        try:
            # SQL to find the maximum numeric part of SKUs that start with 'SKU'
            # and ensure the part after 'SKU' is purely numeric.
            stmt = sql_text("""
                SELECT MAX(TRY_CAST(SUBSTRING(SKU, 4, LEN(SKU) - 3) AS INT))
                FROM StockWeavix.Products
                WHERE SKU LIKE 'SKU%'
                  AND PATINDEX('%[^0-9]%', SUBSTRING(SKU, 4, LEN(SKU) - 3)) = 0;
            """)
            last_sku_numeric_val = db.session.execute(stmt).scalar_one_or_none()

            # If no SKU with 'SKU' prefix exists, start with 1001, otherwise increment
            next_sku_number = (last_sku_numeric_val or 1000) + 1
            generated_sku = f"SKU{next_sku_number}"

            # Check for conflicting SKU in case of parallel operations or deleted SKUs
            conflicting_sku_exists = db.session.query(Product.ProductID).filter(Product.SKU == generated_sku).first()
            if conflicting_sku_exists:
                flash(
                    f'Згенерований SKU "{generated_sku}" вже існує. Це може статися через паралельні операції або якщо останній SKU був видалений. Спробуйте ще раз.',
                    'danger')
                return render_template('products/create_product_form.html',
                                       all_categories=all_categories,
                                       all_manufacturers=all_manufacturers,
                                       form_data=form_data), 500
        except Exception as e_sku:
            db.session.rollback()
            flash(f'Помилка при генерації SKU: {str(e_sku)}', 'danger')
            return render_template('products/create_product_form.html',
                                   all_categories=all_categories,
                                   all_manufacturers=all_manufacturers,
                                   form_data=form_data)

        new_product = Product(
            ProductName=product_name,
            SKU=generated_sku,
            ProductCategoryID=category_id,
            ManufacturerID=manufacturer_id,
            Price=price,
            ProductDescription=description if description else None,
            CreatedDate=datetime.now(timezone.utc),
            LastUpdated=datetime.now(timezone.utc)
        )
        db.session.add(new_product)
        try:
            db.session.commit()
            flash(f'Товар "{new_product.ProductName}" (SKU: {new_product.SKU}) успішно створено.', 'success')
            return redirect(url_for('products_bp.view_product', product_id=new_product.ProductID))
        except Exception as e:
            db.session.rollback()
            if "UQ__Products__DD4E05F2" in str(e) or "unique constraint" in str(e).lower() and "SKU" in str(e).upper():
                flash(
                    f'Помилка: SKU "{generated_sku}" вже існує в базі даних. Можливо, сталася помилка паралельного створення. Спробуйте ще раз.',
                    'danger')
            else:
                flash(f'Помилка при створенні товару: {str(e)}', 'danger')
            return render_template('products/create_product_form.html',
                                   all_categories=all_categories,
                                   all_manufacturers=all_manufacturers,
                                   form_data=form_data)

    return render_template('products/create_product_form.html',
                           all_categories=all_categories,
                           all_manufacturers=all_manufacturers,
                           form_data={})


@products_bp.route('/<int:product_id>/view')
def view_product(product_id):
    product_item = Product.query.options(
        joinedload(Product.category),
        joinedload(Product.manufacturer)
    ).get_or_404(product_id)
    return render_template('products/product_details_view.html', product=product_item)


@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product_to_edit = Product.query.get_or_404(product_id)
    all_categories = ProductCategory.query.order_by(ProductCategory.CategoryName).all()
    all_manufacturers = Manufacturer.query.order_by(Manufacturer.ManufacturerName).all()
    form_data = request.form if request.method == 'POST' else {}

    if request.method == 'POST':
        product_name = request.form.get('product_name', '').strip()
        category_id_str = request.form.get('category_id')
        manufacturer_id_str = request.form.get('manufacturer_id')
        price_str = request.form.get('price', '').replace(',', '.')
        description = request.form.get('description', '').strip()

        if not product_name or not category_id_str:
            flash('Назва товару та категорія є обов\'язковими полями.', 'warning')
            return render_template('products/edit_product_form.html', product=product_to_edit,
                                   all_categories=all_categories, all_manufacturers=all_manufacturers,
                                   form_data=form_data), 400
        try:
            category_id = int(category_id_str)
        except ValueError:
            flash('Некоректне значення для категорії.', 'warning')
            return render_template('products/edit_product_form.html', product=product_to_edit,
                                   all_categories=all_categories, all_manufacturers=all_manufacturers,
                                   form_data=form_data), 400

        manufacturer_id = None
        if manufacturer_id_str and manufacturer_id_str.isdigit():
            manufacturer_id = int(manufacturer_id_str)

        price = None
        if price_str:
            try:
                price_val = decimal.Decimal(price_str)
                if price_val >= 0:
                    price = price_val
                else:
                    flash('Ціна не може бути від\'ємною.', 'warning')
                    return render_template('products/edit_product_form.html', product=product_to_edit,
                                           all_categories=all_categories, all_manufacturers=all_manufacturers,
                                           form_data=form_data), 400
            except decimal.InvalidOperation:
                flash('Некоректний формат ціни.', 'warning')
                return render_template('products/edit_product_form.html', product=product_to_edit,
                                       all_categories=all_categories, all_manufacturers=all_manufacturers,
                                       form_data=form_data), 400

        product_to_edit.ProductName = product_name
        product_to_edit.ProductCategoryID = category_id
        product_to_edit.ManufacturerID = manufacturer_id
        product_to_edit.Price = price
        product_to_edit.ProductDescription = description if description else None
        product_to_edit.LastUpdated = datetime.now(timezone.utc)

        try:
            db.session.commit()
            flash(f'Товар "{product_to_edit.ProductName}" (SKU: {product_to_edit.SKU}) успішно оновлено.', 'success')
            return redirect(url_for('products_bp.view_product', product_id=product_to_edit.ProductID))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при оновленні товару: {str(e)}', 'danger')
            product_to_edit = Product.query.get_or_404(product_id)
            return render_template('products/edit_product_form.html', product=product_to_edit,
                                   all_categories=all_categories, all_manufacturers=all_manufacturers,
                                   form_data=form_data)

    # GET request
    form_data_get = {
        'product_name': product_to_edit.ProductName,
        'sku': product_to_edit.SKU,
        'category_id': product_to_edit.ProductCategoryID,
        'manufacturer_id': product_to_edit.ManufacturerID if product_to_edit.ManufacturerID else '',
        'price': f"{product_to_edit.Price:.2f}" if product_to_edit.Price is not None else '',
        'description': product_to_edit.ProductDescription or ''
    }
    return render_template('products/edit_product_form.html', product=product_to_edit,
                           all_categories=all_categories, all_manufacturers=all_manufacturers,
                           form_data=form_data_get)