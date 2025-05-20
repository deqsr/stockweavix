from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = 'Clients'
    __table_args__ = {'schema': 'Belteh'}
    ClientID      = db.Column(db.Integer, primary_key=True)
    LastName      = db.Column(db.String(100), nullable=False)
    FirstName     = db.Column(db.String(100), nullable=False)
    MiddleName    = db.Column(db.String(100), nullable=True)
    Phone         = db.Column(db.String(50), nullable=True)
    Email         = db.Column(db.String(100), nullable=True)
    Address       = db.Column(db.String(255), nullable=False)
    CreatedDate   = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = db.relationship('Order', back_populates='client')

class City(db.Model):
    __tablename__ = 'Cities'
    __table_args__ = {'schema': 'Belteh'}
    CityID       = db.Column(db.Integer, primary_key=True)
    CityName     = db.Column('CityName', db.String(100), unique=True, nullable=False)
    CreatedDate  = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = db.relationship('Order', back_populates='city')

class Position(db.Model):
    __tablename__ = 'Positions'
    __table_args__ = {'schema': 'Belteh'}
    PositionID   = db.Column(db.Integer, primary_key=True)
    PositionName = db.Column(db.String(100), nullable=False)

    employees = db.relationship('Employee', back_populates='position')

class Warehouse(db.Model):
    __tablename__ = 'Warehouses'
    __table_args__ = {'schema': 'Belteh'}
    WarehouseID   = db.Column(db.Integer, primary_key=True)
    WarehouseName = db.Column(db.String(150), nullable=False)
    Description   = db.Column(db.String, nullable=True)
    Address       = db.Column(db.String, nullable=True)
    CreatedDate   = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employees = db.relationship('Employee', back_populates='warehouse')
    locations = db.relationship('Location', back_populates='warehouse')  # полиці/локації
    zones = db.relationship('Zone', back_populates='warehouse')

class Employee(db.Model):
    __tablename__ = 'Employees'
    __table_args__ = {'schema': 'Belteh'}
    EmployeeID        = db.Column(db.Integer, primary_key=True)
    PositionID        = db.Column(db.Integer, db.ForeignKey('Belteh.Positions.PositionID'), nullable=False)
    WarehouseID       = db.Column(db.Integer, db.ForeignKey('Belteh.Warehouses.WarehouseID'), nullable=False)
    EmployeeLastName  = db.Column(db.String(100), nullable=False)
    EmployeeFirstName = db.Column(db.String(100), nullable=False)
    EmployeePatronymic = db.Column(db.String(100), nullable=True)
    EmployeePassport  = db.Column(db.String(50), nullable=True)
    EmployeePhone     = db.Column(db.String(50), nullable=True)
    EmployeeEmail     = db.Column(db.String(100), nullable=True)
    CreatedDate       = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    position  = db.relationship('Position', back_populates='employees')
    warehouse = db.relationship('Warehouse', back_populates='employees')

class Zone(db.Model):
    __tablename__ = 'Zones'
    __table_args__ = {'schema': 'Belteh'}
    ZoneID      = db.Column(db.Integer, primary_key=True)
    ZoneCode    = db.Column(db.Integer, nullable=False)
    ZoneName    = db.Column(db.String(100), nullable=False)
    WarehouseID = db.Column(db.Integer, db.ForeignKey('Belteh.Warehouses.WarehouseID'), nullable=False)
    RowMin      = db.Column(db.Integer, nullable=False)
    RowMax      = db.Column(db.Integer, nullable=False)
    Description = db.Column(db.String, nullable=True)
    CreatedDate = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = db.relationship('Warehouse', back_populates='zones')
    rows      = db.relationship('ZoneRow', back_populates='zone')

class ZoneRow(db.Model):
    __tablename__ = 'ZoneRows'
    __table_args__ = {'schema': 'Belteh'}
    ZoneRowID = db.Column(db.Integer, primary_key=True)
    ZoneID    = db.Column(db.Integer, db.ForeignKey('Belteh.Zones.ZoneID'), nullable=False)
    RowNumber = db.Column(db.Integer, nullable=False)

    zone  = db.relationship('Zone', back_populates='rows')
    locations = db.relationship('Location', back_populates='row')

class Location(db.Model):
    __tablename__ = 'Locations'
    __table_args__ = {'schema': 'Belteh'}
    LocationID      = db.Column(db.Integer, primary_key=True)
    WarehouseID     = db.Column(db.Integer, db.ForeignKey('Belteh.Warehouses.WarehouseID'), nullable=True)
    ZoneRowID       = db.Column(db.Integer, db.ForeignKey('Belteh.ZoneRows.ZoneRowID'), nullable=True)
    SectionID       = db.Column(db.Integer, db.ForeignKey('Belteh.ZoneSections.SectionID'), nullable=True)
    ShelfID         = db.Column(db.Integer, db.ForeignKey('Belteh.ZoneShelves.ShelfID'), nullable=True)
    CreatedDate     = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdatedDate = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = db.relationship('Warehouse', back_populates='locations')
    row       = db.relationship('ZoneRow', back_populates='locations')
    section   = db.relationship('ZoneSection', back_populates='locations')
    shelf     = db.relationship('ZoneShelf', back_populates='locations')
    inventory_items = db.relationship('Inventory', back_populates='location')

class ZoneSection(db.Model):
    __tablename__ = 'ZoneSections'
    __table_args__ = {'schema': 'Belteh'}
    SectionID     = db.Column(db.Integer, primary_key=True)
    SectionNumber = db.Column(db.Integer, nullable=False)
    locations     = db.relationship('Location', back_populates='section')

class ZoneShelf(db.Model):
    __tablename__ = 'ZoneShelves'
    __table_args__ = {'schema': 'Belteh'}
    ShelfID     = db.Column(db.Integer, primary_key=True)
    ShelfLevel  = db.Column(db.Integer, nullable=False)
    locations   = db.relationship('Location', back_populates='shelf')

class Manufacturer(db.Model):
    __tablename__ = 'Manufacturers'
    __table_args__ = {'schema': 'Belteh'}
    ManufacturerID          = db.Column(db.Integer, primary_key=True)
    ManufacturerName        = db.Column(db.String(150), nullable=False)
    ManufacturerDescription = db.Column(db.String, nullable=True)
    CreatedDate             = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated             = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = db.relationship('Product', back_populates='manufacturer')

class ProductCategory(db.Model):
    __tablename__ = 'ProductCategories'
    __table_args__ = {'schema': 'Belteh'}
    CategoryID    = db.Column(db.Integer, primary_key=True)
    CategoryName  = db.Column(db.String(100), nullable=False)
    Description   = db.Column(db.String, nullable=True)
    CreatedDate   = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = db.relationship('Product', back_populates='category')

class Product(db.Model):
    __tablename__ = 'Products'
    __table_args__ = {'schema': 'Belteh'}
    ProductID         = db.Column(db.Integer, primary_key=True)
    ProductName       = db.Column(db.String(150), nullable=False)
    ManufacturerID    = db.Column(db.Integer, db.ForeignKey('Belteh.Manufacturers.ManufacturerID'), nullable=True)
    ProductCategoryID = db.Column(db.Integer, db.ForeignKey('Belteh.ProductCategories.CategoryID'), nullable=False)
    ProductDescription= db.Column(db.String, nullable=True)
    SKU               = db.Column(db.String(50), unique=True, nullable=False)
    Price             = db.Column(db.Numeric, nullable=True)
    CreatedDate       = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    manufacturer     = db.relationship('Manufacturer', back_populates='products')
    category         = db.relationship('ProductCategory', back_populates='products')
    inventory_items  = db.relationship('Inventory', back_populates='product')
    order_items      = db.relationship('OrderItem', back_populates='product')
    supply_details   = db.relationship('SupplyDetail', back_populates='product')

class Inventory(db.Model):
    __tablename__ = 'Inventory'
    __table_args__ = {'schema': 'Belteh'}
    InventoryID  = db.Column(db.Integer, primary_key=True)
    ProductID    = db.Column(db.Integer, db.ForeignKey('Belteh.Products.ProductID'), nullable=False)
    LocationID   = db.Column(db.Integer, db.ForeignKey('Belteh.Locations.LocationID'), nullable=False)
    Quantity     = db.Column(db.Integer, nullable=False)
    LastUpdated  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product      = db.relationship('Product', back_populates='inventory_items')
    location     = db.relationship('Location', back_populates='inventory_items')

class OrderStatus(db.Model):
    __tablename__ = 'OrderStatuses'
    __table_args__ = {'schema': 'Belteh'}
    OrderStatusID = db.Column(db.Integer, primary_key=True)
    StatusName    = db.Column(db.String(50), nullable=False)

    orders = db.relationship('Order', back_populates='status')

class Order(db.Model):
    __tablename__ = 'Orders'
    __table_args__ = {'schema': 'Belteh'}
    OrderID       = db.Column(db.Integer, primary_key=True)
    ClientID      = db.Column(db.Integer, db.ForeignKey('Belteh.Clients.ClientID'), nullable=True)
    CityID        = db.Column(db.Integer, db.ForeignKey('Belteh.Cities.CityID'), nullable=True)
    OrderDate     = db.Column(db.Date, nullable=False)
    PaymentDate   = db.Column(db.Date, nullable=True)
    Address = db.Column(db.String(255), nullable=True)
    OrderStatusID = db.Column(db.Integer, db.ForeignKey('Belteh.OrderStatuses.OrderStatusID'), nullable=False)
    Description = db.Column(db.String, nullable=True)
    CreatedDate   = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client        = db.relationship('Client', back_populates='orders')
    city          = db.relationship('City', back_populates='orders')
    status        = db.relationship('OrderStatus', back_populates='orders')
    items         = db.relationship('OrderItem', back_populates='order')

class OrderItem(db.Model):
    __tablename__ = 'OrderItems'
    __table_args__ = {'schema': 'Belteh'}
    OrderItemID = db.Column(db.Integer, primary_key=True)
    OrderID     = db.Column(db.Integer, db.ForeignKey('Belteh.Orders.OrderID'), nullable=False)
    ProductID   = db.Column(db.Integer, db.ForeignKey('Belteh.Products.ProductID'), nullable=False)
    Quantity    = db.Column(db.Integer, nullable=False)
    UnitPrice   = db.Column(db.Numeric, nullable=False)

    order       = db.relationship('Order', back_populates='items')
    product     = db.relationship('Product', back_populates='order_items')

class Supplier(db.Model):
    __tablename__ = 'Suppliers'
    __table_args__ = {'schema': 'Belteh'}
    SupplierID     = db.Column(db.Integer, primary_key=True)
    SupplierName   = db.Column(db.String(150), nullable=False)
    SupplierAddress= db.Column(db.String, nullable=True)
    SupplierPhone  = db.Column(db.String(50), nullable=True)
    SupplierEDRPOU = db.Column(db.String(50), nullable=True)
    SupplierMFI    = db.Column(db.String(50), nullable=True)
    ContactPerson  = db.Column(db.String(100), nullable=True)
    CreatedDate    = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contracts      = db.relationship('SupplyContracts', back_populates='supplier')

class SupplyStatus(db.Model):
    __tablename__ = 'SupplyStatuses'
    __table_args__ = {'schema': 'Belteh'}
    SupplyStatusID= db.Column(db.Integer, primary_key=True)
    StatusName    = db.Column(db.String(50), nullable=False)

    contracts     = db.relationship('SupplyContracts', back_populates='status')

class SupplyContracts(db.Model):
    __tablename__ = 'SupplyContracts'
    __table_args__ = {'schema': 'Belteh'}
    SupplyID        = db.Column(db.Integer, primary_key=True)
    SupplierID      = db.Column(db.Integer, db.ForeignKey('Belteh.Suppliers.SupplierID'), nullable=False)
    ContractPrice   = db.Column(db.Numeric, nullable=True)
    PaymentDate     = db.Column(db.Date, nullable=True)
    SupplyStatusID  = db.Column(db.Integer, db.ForeignKey('Belteh.SupplyStatuses.SupplyStatusID'), nullable=False)
    Description     = db.Column(db.String, nullable=True)
    CreatedDate     = db.Column(db.DateTime, default=datetime.utcnow)
    LastUpdated     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier        = db.relationship('Supplier', back_populates='contracts')
    status          = db.relationship('SupplyStatus', back_populates='contracts')
    details         = db.relationship('SupplyDetail', back_populates='contract')

class SupplyDetail(db.Model):
    __tablename__ = 'SupplyDetails'
    __table_args__ = {'schema': 'Belteh'}
    SupplyDetailID = db.Column(db.Integer, primary_key=True)
    SupplyID       = db.Column(db.Integer, db.ForeignKey('Belteh.SupplyContracts.SupplyID'), nullable=False)
    ProductID      = db.Column(db.Integer, db.ForeignKey('Belteh.Products.ProductID'), nullable=False)
    Quantity       = db.Column(db.Integer, nullable=False)
    UnitPrice      = db.Column(db.Numeric, nullable=True)

    contract = db.relationship('SupplyContracts', back_populates='details')
    product  = db.relationship('Product', back_populates='supply_details')

class LocationStatusView(db.Model):
    __tablename__ = 'vw_LocationStatus'
    __table_args__ = {'schema': 'Belteh', 'extend_existing': True}

    LocationID    = db.Column(db.Integer, primary_key=True)
    ZoneCode      = db.Column(db.Integer)
    RowNumber     = db.Column(db.Integer)
    SectionNumber = db.Column(db.Integer)
    ShelfLevel    = db.Column(db.Integer)
    TotalQuantity = db.Column(db.Integer)
    ShelfStatus   = db.Column(db.String)

    def __repr__(self):
        return (
            f"<LocationStatusView "
            f"{self.LocationID=} Zone={self.ZoneCode} Row={self.RowNumber} "
            f"Shelf={self.ShelfLevel} Qty={self.TotalQuantity} Status={self.ShelfStatus}>"
        )

class ZoneOccupancyView(db.Model):
    __tablename__ = 'ZoneOccupancyView'
    __table_args__ = {'schema': 'Belteh'}

    ZoneID = db.Column(db.Integer, primary_key=True)
    TotalLocations = db.Column(db.Integer)
    OccupiedLocations = db.Column(db.Integer)
    OccupancyPercentage = db.Column(db.Float)