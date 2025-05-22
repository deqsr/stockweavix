from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Date, Numeric, ForeignKey, Text, Float as SQLAlchemyFloat, Index, UniqueConstraint
from sqlalchemy.dialects.mssql import DATETIME2 # Для Location дат
from datetime import datetime, date, timezone

import decimal

db = SQLAlchemy()

# Допоміжна функція для server_default, щоб уникнути проблем з lambda в деяких версіях
def default_utc_now():
    return datetime.now(timezone.utc)

class City(db.Model):
    __tablename__ = 'Cities'
    __table_args__ = (
        db.PrimaryKeyConstraint('CityID', name='PK__Cities__F2D21A96E70C87F2'),
        {'schema': 'StockWeavix'}
    )

    CityID: Mapped[int] = mapped_column(Integer, primary_key=True)
    CityName: Mapped[str] = mapped_column(String(100), unique=True)
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'))
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now) # onupdate для Flask

    orders: Mapped[list[Order]] = relationship('Order', back_populates='city')

class Client(db.Model):
    __tablename__ = 'Clients'
    __table_args__ = (
        db.PrimaryKeyConstraint('ClientID', name='PK__Clients__E67E1A04246819A8'),
        {'schema': 'StockWeavix'}
    )

    ClientID: Mapped[int] = mapped_column(Integer, primary_key=True)
    LastName: Mapped[str] = mapped_column(String(50), server_default=db.text("('Невідомо')"))
    FirstName: Mapped[str] = mapped_column(String(50), server_default=db.text("('Невідомо')"))
    Address: Mapped[str] = mapped_column(String(500), server_default=db.text("('Не вказано')"))
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, default=default_utc_now)
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, default=default_utc_now, onupdate=default_utc_now)
    MiddleName: Mapped[str | None] = mapped_column(String(50), nullable=True)
    Phone: Mapped[str | None] = mapped_column(String(15), nullable=True)
    Email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    orders: Mapped[list[Order]] = relationship('Order', back_populates='client')

class Manufacturer(db.Model):
    __tablename__ = 'Manufacturers'
    __table_args__ = (
        db.PrimaryKeyConstraint('ManufacturerID', name='PK__Manufact__357E5CA10335A6E8'),
        {'schema': 'StockWeavix'}
    )

    ManufacturerID: Mapped[int] = mapped_column(Integer, primary_key=True)
    ManufacturerName: Mapped[str] = mapped_column(String(255))
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'))
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now)
    ManufacturerDescription: Mapped[str | None] = mapped_column(String(500), nullable=True)

    products: Mapped[list[Product]] = relationship('Product', back_populates='manufacturer')

class OrderStatus(db.Model):
    __tablename__ = 'OrderStatuses'
    __table_args__ = (
        db.PrimaryKeyConstraint('OrderStatusID', name='PK__OrderSta__BC674F4139D5CCFE'),
        {'schema': 'StockWeavix'}
    )

    OrderStatusID: Mapped[int] = mapped_column(Integer, primary_key=True)
    StatusName: Mapped[str] = mapped_column(String(255))

    orders: Mapped[list[Order]] = relationship('Order', back_populates='status')

class Position(db.Model):
    __tablename__ = 'Positions'
    __table_args__ = (
        db.PrimaryKeyConstraint('PositionID', name='PK__Position__60BB9A596E5A2324'),
        {'schema': 'StockWeavix'}
    )

    PositionID: Mapped[int] = mapped_column(Integer, primary_key=True)
    PositionName: Mapped[str] = mapped_column(String(255))
    employees: Mapped[list[Employee]] = relationship('Employee', back_populates='position')

class ProductCategory(db.Model):
    __tablename__ = 'ProductCategories'
    __table_args__ = (
        db.PrimaryKeyConstraint('CategoryID', name='PK__ProductC__19093A2BC48B73DF'),
        {'schema': 'StockWeavix'}
    )

    CategoryID: Mapped[int] = mapped_column(Integer, primary_key=True)
    CategoryName: Mapped[str] = mapped_column(String(255))
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'))
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now)
    Description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    products: Mapped[list[Product]] = relationship('Product', back_populates='category')

class Supplier(db.Model):
    __tablename__ = 'Suppliers'
    __table_args__ = (
        db.PrimaryKeyConstraint('SupplierID', name='PK__Supplier__4BE66694CE91E7F7'),
        {'schema': 'StockWeavix'}
    )

    SupplierID: Mapped[int] = mapped_column(Integer, primary_key=True)
    SupplierName: Mapped[str] = mapped_column(String(255))
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'))
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now)
    SupplierAddress: Mapped[str | None] = mapped_column(String(255), nullable=True)
    SupplierPhone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    SupplierEDRPOU: Mapped[str | None] = mapped_column(String(50), nullable=True)
    SupplierMFI: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ContactPerson: Mapped[str | None] = mapped_column(String(255), nullable=True)

    contracts: Mapped[list[SupplyContract]] = relationship('SupplyContract', back_populates='supplier')

class SupplyStatus(db.Model): # Змінив SupplyStatuses на SupplyStatus
    __tablename__ = 'SupplyStatuses'
    __table_args__ = (
        db.PrimaryKeyConstraint('SupplyStatusID', name='PK__Contract__96D70656FDDE505B'),
        {'schema': 'StockWeavix'}
    )

    SupplyStatusID: Mapped[int] = mapped_column(Integer, primary_key=True)
    StatusName: Mapped[str] = mapped_column(String(255))
    CssClassName: Mapped[str | None] = mapped_column(String(50), nullable=True)

    contracts: Mapped[list[SupplyContract]] = relationship('SupplyContract', back_populates='status')

class Warehouse(db.Model):
    __tablename__ = 'Warehouses'
    __table_args__ = (
        db.PrimaryKeyConstraint('WarehouseID', name='PK__Warehous__2608AFD922FDC967'),
        {'schema': 'StockWeavix'}
    )

    WarehouseID: Mapped[int] = mapped_column(Integer, primary_key=True)
    WarehouseName: Mapped[str] = mapped_column(String(255))
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'))
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now)
    Description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    Address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    employees: Mapped[list[Employee]] = relationship('Employee', back_populates='warehouse')
    zones: Mapped[list[Zone]] = relationship('Zone', back_populates='warehouse')
    locations: Mapped[list[Location]] = relationship('Location', back_populates='warehouse')

class ZoneSection(db.Model): # Змінив ZoneSections на ZoneSection
    __tablename__ = 'ZoneSections'
    __table_args__ = (
        db.PrimaryKeyConstraint('SectionID', name='PK__ZoneSect__80EF0892ED46AC0D'),
        db.Index('UQ__ZoneSect__B6D6EE018FE38E67', 'SectionNumber', unique=True),
        {'schema': 'StockWeavix'}
    )

    SectionID: Mapped[int] = mapped_column(Integer, primary_key=True)
    SectionNumber: Mapped[int] = mapped_column(Integer)

    locations: Mapped[list[Location]] = relationship('Location', back_populates='section')

class ZoneShelf(db.Model): # Змінив ZoneShelves на ZoneShelf
    __tablename__ = 'ZoneShelves'
    __table_args__ = (
        db.PrimaryKeyConstraint('ShelfID', name='PK__ZoneShel__DBD04F27FA0BAB71'),
        db.Index('UQ__ZoneShel__AFFEC82EC9B3E5AC', 'ShelfLevel', unique=True),
        {'schema': 'StockWeavix'}
    )

    ShelfID: Mapped[int] = mapped_column(Integer, primary_key=True)
    ShelfLevel: Mapped[int] = mapped_column(Integer)

    locations: Mapped[list[Location]] = relationship('Location', back_populates='shelf')

class Employee(db.Model):
    __tablename__ = 'Employees'
    __table_args__ = (
        db.ForeignKeyConstraint(['PositionID'], ['StockWeavix.Positions.PositionID'], name='FK_Employees_Positions'),
        db.ForeignKeyConstraint(['WarehouseID'], ['StockWeavix.Warehouses.WarehouseID'], name='FK_Employees_Warehouses'),
        db.PrimaryKeyConstraint('EmployeeID', name='PK__Employee__7AD04FF178670A77'),
        {'schema': 'StockWeavix'}
    )

    EmployeeID: Mapped[int] = mapped_column(Integer, primary_key=True)
    PositionID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Positions.PositionID'))
    WarehouseID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Warehouses.WarehouseID'))
    EmployeeLastName: Mapped[str] = mapped_column(String(255))
    EmployeeFirstName: Mapped[str] = mapped_column(String(255))
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'))
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now)
    EmployeePatronymic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    EmployeePassport: Mapped[str | None] = mapped_column(String(50), nullable=True)
    EmployeePhone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    EmployeeEmail: Mapped[str | None] = mapped_column(String(255), nullable=True)

    position: Mapped[Position] = relationship('Position', back_populates='employees')
    warehouse: Mapped[Warehouse] = relationship('Warehouse', back_populates='employees')

class Order(db.Model):
    __tablename__ = 'Orders'
    OrderID: Mapped[int] = mapped_column(Integer, primary_key=True)
    ClientID: Mapped[int | None] = mapped_column(ForeignKey('StockWeavix.Clients.ClientID'), nullable=True)
    CityID: Mapped[int | None] = mapped_column(ForeignKey('StockWeavix.Cities.CityID'), nullable=True) # Якщо є
    OrderDate: Mapped[date] = mapped_column(Date, default=date.today) # Поточна дата за замовчуванням
    OrderStatusID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.OrderStatuses.OrderStatusID'))
    OrderTotal: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 2), nullable=True, default=0.00) # Додаємо поле для суми
    Description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ShippingAddress: Mapped[str | None] = mapped_column(String(500), nullable=True) # Додамо адресу доставки
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, default=default_utc_now)
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, default=default_utc_now, onupdate=default_utc_now)

    client: Mapped[Client | None] = relationship(back_populates='orders')
    status: Mapped[OrderStatus] = relationship(back_populates='orders')
    city: Mapped[City | None] = relationship(back_populates='orders') # Якщо є
    items: Mapped[list['OrderItem']] = relationship(back_populates='order', cascade="all, delete-orphan")

    # Метод для перерахунку суми замовлення (приклад)
    def calculate_total(self):
        total = decimal.Decimal('0.00')
        for item in self.items:
            if item.Quantity and item.UnitPrice:
                total += decimal.Decimal(str(item.Quantity)) * decimal.Decimal(str(item.UnitPrice))
        self.OrderTotal = total
        return total

class Product(db.Model):
    __tablename__ = 'Products'
    __table_args__ = (
        db.ForeignKeyConstraint(['ManufacturerID'], ['StockWeavix.Manufacturers.ManufacturerID'], name='FK_Products_Manufacturers'),
        db.ForeignKeyConstraint(['ProductCategoryID'], ['StockWeavix.ProductCategories.CategoryID'], name='FK_Products_ProductCategories'),
        db.PrimaryKeyConstraint('ProductID', name='PK__Products__B40CC6ED93612CFE'),
        db.UniqueConstraint('SKU', name='UQ__Products__DD4E05F2xxxxxxx'),
        {'schema': 'StockWeavix'}
    )

    ProductID: Mapped[int] = mapped_column(Integer, primary_key=True)
    ProductName: Mapped[str] = mapped_column(String(255))
    ProductCategoryID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.ProductCategories.CategoryID'))
    SKU: Mapped[str] = mapped_column(String(100), unique=True)
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'))
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now)
    ManufacturerID: Mapped[int | None] = mapped_column(ForeignKey('StockWeavix.Manufacturers.ManufacturerID'), nullable=True)
    ProductDescription: Mapped[str | None] = mapped_column(String(500), nullable=True)
    Price: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    manufacturer: Mapped[Manufacturer | None] = relationship('Manufacturer', back_populates='products')
    category: Mapped[ProductCategory] = relationship('ProductCategory', back_populates='products')
    order_items: Mapped[list[OrderItem]] = relationship('OrderItem', back_populates='product')
    supply_details: Mapped[list[SupplyDetail]] = relationship('SupplyDetail', back_populates='product')
    inventory_items: Mapped[list[Inventory]] = relationship('Inventory', back_populates='product')

class SupplyContract(db.Model):
    __tablename__ = 'SupplyContracts'
    __table_args__ = (
        db.ForeignKeyConstraint(['SupplierID'], ['StockWeavix.Suppliers.SupplierID'], name='FK_SupplyContracts_Suppliers'),
        db.ForeignKeyConstraint(['SupplyStatusID'], ['StockWeavix.SupplyStatuses.SupplyStatusID'], name='FK_SupplyContracts_SupplyStatuses'),
        db.PrimaryKeyConstraint('SupplyID', name='PK__SupplyCo__C90D3409B87C0427'),
        {'schema': 'StockWeavix'}
    )

    SupplyID: Mapped[int] = mapped_column(Integer, primary_key=True)
    SupplierID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Suppliers.SupplierID'))
    SupplyStatusID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.SupplyStatuses.SupplyStatusID'))
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'))
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now)
    ContractPrice: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    PaymentDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    Description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    supplier: Mapped[Supplier] = relationship('Supplier', back_populates='contracts')
    status: Mapped[SupplyStatus] = relationship('SupplyStatus', back_populates='contracts')
    details: Mapped[list[SupplyDetail]] = relationship('SupplyDetail', back_populates='contract')

class Zone(db.Model):
    __tablename__ = 'Zones'
    __table_args__ = (
        db.ForeignKeyConstraint(['WarehouseID'], ['StockWeavix.Warehouses.WarehouseID'], name='FK_Zones_Warehouses'),
        db.PrimaryKeyConstraint('ZoneID', name='PK__Zones__60166795A2BA06ED'),
        {'schema': 'StockWeavix'}
    )

    ZoneID: Mapped[int] = mapped_column(Integer, primary_key=True)
    ZoneCode: Mapped[int] = mapped_column(Integer)
    ZoneName: Mapped[str] = mapped_column(String(255))
    WarehouseID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Warehouses.WarehouseID'))
    RowMin: Mapped[int] = mapped_column(Integer)
    RowMax: Mapped[int] = mapped_column(Integer)
    CreatedDate: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'))
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now)
    Description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    warehouse: Mapped[Warehouse] = relationship('Warehouse', back_populates='zones')
    rows: Mapped[list[ZoneRow]] = relationship('ZoneRow', back_populates='zone')

class OrderItem(db.Model):
    __tablename__ = 'OrderItems'
    __table_args__ = (
        db.ForeignKeyConstraint(['OrderID'], ['StockWeavix.Orders.OrderID'], name='FK_OrderItems_Orders'),
        db.ForeignKeyConstraint(['ProductID'], ['StockWeavix.Products.ProductID'], name='FK_OrderItems_Products'),
        db.PrimaryKeyConstraint('OrderItemID', name='PK__OrderIte__57ED06A11A488A57'),
        {'schema': 'StockWeavix'}
    )

    OrderItemID: Mapped[int] = mapped_column(Integer, primary_key=True)
    OrderID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Orders.OrderID'))
    ProductID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Products.ProductID'))
    Quantity: Mapped[int] = mapped_column(Integer)
    UnitPrice: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped[Order] = relationship('Order', back_populates='items')
    product: Mapped[Product] = relationship('Product', back_populates='order_items')

    Order.items = relationship('OrderItem', back_populates='order')


class SupplyDetail(db.Model):
    __tablename__ = 'SupplyDetails'
    __table_args__ = (
        db.ForeignKeyConstraint(['ProductID'], ['StockWeavix.Products.ProductID'], name='FK_SupplyDetails_Products'),
        db.ForeignKeyConstraint(['SupplyID'], ['StockWeavix.SupplyContracts.SupplyID'], name='FK_SupplyDetails_SupplyContracts'),
        db.PrimaryKeyConstraint('SupplyDetailID', name='PK__Contract__CCA7AF02BA495A24'),
        {'schema': 'StockWeavix'}
    )

    SupplyDetailID: Mapped[int] = mapped_column(Integer, primary_key=True)
    SupplyID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.SupplyContracts.SupplyID'))
    ProductID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Products.ProductID'))
    Quantity: Mapped[int] = mapped_column(Integer)
    UnitPrice: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    product: Mapped[Product] = relationship('Product', back_populates='supply_details')
    contract: Mapped[SupplyContract] = relationship('SupplyContract', back_populates='details')

class ZoneRow(db.Model):
    __tablename__ = 'ZoneRows'
    __table_args__ = (
        db.ForeignKeyConstraint(['ZoneID'], ['StockWeavix.Zones.ZoneID'], name='FK_ZoneRows_Zones'),
        db.PrimaryKeyConstraint('ZoneRowID', name='PK__ZoneRows__A94FAD68D04FF7C1'),
        db.Index('UQ_ZoneRows_Zone_Row', 'ZoneID', 'RowNumber', unique=True),
        {'schema': 'StockWeavix'}
    )

    ZoneRowID: Mapped[int] = mapped_column(Integer, primary_key=True)
    ZoneID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Zones.ZoneID'))
    RowNumber: Mapped[int] = mapped_column(Integer)

    zone: Mapped[Zone] = relationship('Zone', back_populates='rows')
    locations: Mapped[list[Location]] = relationship('Location', back_populates='row')

class Location(db.Model):
    __tablename__ = 'Locations'
    __table_args__ = (
        db.ForeignKeyConstraint(['SectionID'], ['StockWeavix.ZoneSections.SectionID'], name='FK_Locations_ZoneSection'),
        db.ForeignKeyConstraint(['ShelfID'], ['StockWeavix.ZoneShelves.ShelfID'], name='FK_Locations_ZoneShelf'),
        db.ForeignKeyConstraint(['WarehouseID'], ['StockWeavix.Warehouses.WarehouseID'], name='FK_Locations_Warehouse'),
        db.ForeignKeyConstraint(['ZoneRowID'], ['StockWeavix.ZoneRows.ZoneRowID'], name='FK_Locations_ZoneRow'),
        db.PrimaryKeyConstraint('LocationID', name='PK__Location__E7FEA477C0CF483D'),
        {'schema': 'StockWeavix'}
    )

    LocationID: Mapped[int] = mapped_column(Integer, primary_key=True)
    CreatedDate: Mapped[datetime] = mapped_column(DATETIME2, server_default=db.text('(getdate())'))
    LastUpdatedDate: Mapped[datetime] = mapped_column(DATETIME2, server_default=db.text('(getdate())'), onupdate=default_utc_now)
    WarehouseID: Mapped[int | None] = mapped_column(ForeignKey('StockWeavix.Warehouses.WarehouseID'), nullable=True)
    ZoneRowID: Mapped[int | None] = mapped_column(ForeignKey('StockWeavix.ZoneRows.ZoneRowID'), nullable=True)
    SectionID: Mapped[int | None] = mapped_column(ForeignKey('StockWeavix.ZoneSections.SectionID'), nullable=True)
    ShelfID: Mapped[int | None] = mapped_column(ForeignKey('StockWeavix.ZoneShelves.ShelfID'), nullable=True)

    warehouse: Mapped[Warehouse | None] = relationship('Warehouse', back_populates='locations')
    row: Mapped[ZoneRow | None] = relationship('ZoneRow', back_populates='locations')
    section: Mapped[ZoneSection | None] = relationship('ZoneSection', back_populates='locations')
    shelf: Mapped[ZoneShelf | None] = relationship('ZoneShelf', back_populates='locations')
    inventory_items: Mapped[list[Inventory]] = relationship('Inventory', back_populates='location')

    def full_address(self) -> str:
        parts: list[str] = []
        current_row = self.row
        if current_row:
            current_zone = current_row.zone
            if current_zone:
                parts.append(f"Зона: {current_zone.ZoneCode}")
            parts.append(f"Ряд: {current_row.RowNumber}")
        current_section = self.section
        if current_section:
            parts.append(f"Секція: {current_section.SectionNumber}")
        current_shelf = self.shelf
        if current_shelf:
            parts.append(f"Полиця: {current_shelf.ShelfLevel}")
        address_str = ", ".join(parts)
        if not address_str and self.warehouse:
            current_warehouse = self.warehouse
            if current_warehouse:
                return f"Склад: {current_warehouse.WarehouseName}"
        if not address_str:
            return "N/A"
        return address_str

class Inventory(db.Model):
    __tablename__ = 'Inventory'
    __table_args__ = (
        db.ForeignKeyConstraint(['LocationID'], ['StockWeavix.Locations.LocationID'], name='FK_Inventory_Locations'),
        db.ForeignKeyConstraint(['ProductID'], ['StockWeavix.Products.ProductID'], name='FK_Inventory_Products'),
        db.PrimaryKeyConstraint('InventoryID', name='PK__Inventor__F5FDE6D3B1869395'),
        {'schema': 'StockWeavix'}
    )

    InventoryID: Mapped[int] = mapped_column(Integer, primary_key=True)
    ProductID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Products.ProductID'))
    LocationID: Mapped[int] = mapped_column(ForeignKey('StockWeavix.Locations.LocationID'))
    Quantity: Mapped[int] = mapped_column(Integer)
    LastUpdated: Mapped[datetime] = mapped_column(DateTime, server_default=db.text('(getdate())'), onupdate=default_utc_now)

    location: Mapped[Location] = relationship('Location', back_populates='inventory_items')
    product: Mapped[Product] = relationship('Product', back_populates='inventory_items')

class LocationStatusView(db.Model):
    __tablename__ = 'vw_LocationStatus'
    __table_args__ = ({'schema': 'StockWeavix', 'info': {'is_view': True}})
    LocationID: Mapped[int] = mapped_column(Integer, primary_key=True)
    ZoneCode: Mapped[int | None] = mapped_column(Integer, nullable=True)
    RowNumber: Mapped[int | None] = mapped_column(Integer, nullable=True)
    SectionNumber: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ShelfLevel: Mapped[int | None] = mapped_column(Integer, nullable=True)
    TotalQuantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ShelfStatus: Mapped[str | None] = mapped_column(String(16), nullable=True)

class ZoneOccupancyView(db.Model):
    __tablename__ = 'ZoneOccupancyView'
    __table_args__ = ({'schema': 'StockWeavix', 'info': {'is_view': True}})
    ZoneID: Mapped[int] = mapped_column(Integer, primary_key=True)
    TotalLocations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    OccupiedLocations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    OccupancyPercentage: Mapped[float | None] = mapped_column(SQLAlchemyFloat(precision=53), nullable=True)


class User:
    pass