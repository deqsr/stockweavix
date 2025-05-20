# app/routes/inventory.py

from flask import Blueprint, render_template, request
from app.models import Inventory, Product, ProductCategory


inv_bp = Blueprint('inventory', __name__)

@inv_bp.route('/', methods=['GET'])
def list_inventory():
    cat_id = request.args.get('category', type=int)
    categories = ProductCategory.query.order_by(ProductCategory.CategoryName).all()

    # Базовий запит — приєднуємо таблицю Products
    query = Inventory.query.join(Product, Inventory.ProductID == Product.ProductID)

    # Якщо в URL передано category, ставимо WHERE
    if cat_id:
        query = query.filter(Product.ProductCategoryID == cat_id)

    items = query.all()

    return render_template(
        'inventory_list.html',
        items=items,
        categories=categories,
        selected_category=cat_id
    )

