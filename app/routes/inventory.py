from flask import Blueprint, render_template, request, url_for
from app.models import db, Inventory, Product, ProductCategory, Manufacturer, Location, ZoneRow, Zone, ZoneSection
from sqlalchemy.orm import joinedload


inv_bp = Blueprint('inv_bp', __name__)


@inv_bp.route('/')
def inventory_list():
    page = request.args.get('page', 1, type=int)
    per_page = 15  # Кількість елементів на сторінці

    cat_id_str = request.args.get('category_id', '')  # Змінив 'category' на 'category_id'
    cat_id = int(cat_id_str) if cat_id_str.isdigit() else None

    all_categories_for_filter = ProductCategory.query.order_by(ProductCategory.CategoryName).all()

    query = Inventory.query.options(
        joinedload(Inventory.product).joinedload(Product.category),  # Завантажуємо товар та його категорію
        joinedload(Inventory.product).joinedload(Product.manufacturer),  # Завантажуємо виробника товару
        joinedload(Inventory.location).joinedload(Location.row).joinedload(ZoneRow.zone),
        # Завантажуємо локацію -> ряд -> зону
        joinedload(Inventory.location).joinedload(Location.section),
        joinedload(Inventory.location).joinedload(Location.shelf)
    )

    if cat_id:
        query = query.join(Product, Inventory.ProductID == Product.ProductID) \
            .filter(Product.ProductCategoryID == cat_id)

    if not cat_id:  # Якщо фільтра не було, Product ще не приєднаний для сортування
        query = query.join(Product, Inventory.ProductID == Product.ProductID)

    pagination = query.order_by(Product.ProductName).paginate(page=page, per_page=per_page, error_out=False)


    return render_template(
        'inventory_list.html',
        pagination=pagination,  # Передаємо об'єкт пагінації
        all_categories_for_filter=all_categories_for_filter,
        selected_category_id=cat_id
    )