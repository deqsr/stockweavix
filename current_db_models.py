from typing import List, Optional

from sqlalchemy import Column, DECIMAL, Date, DateTime, Float, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Table, Unicode, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import decimal

class Base(DeclarativeBase):
    pass


class Cities(Base):
    __tablename__ = 'Cities'
    __table_args__ = (
        PrimaryKeyConstraint('CityID', name='PK__Cities__F2D21A96E70C87F2'),
        {'schema': 'StockWeavix'}
    )

    CityID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    CityName: Mapped[str] = mapped_column(Unicode(100, 'Cyrillic_General_CI_AS'))
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))

    Orders: Mapped[List['Orders']] = relationship('Orders', back_populates='Cities_')


class Clients(Base):
    __tablename__ = 'Clients'
    __table_args__ = (
        PrimaryKeyConstraint('ClientID', name='PK__Clients__E67E1A04246819A8'),
        {'schema': 'StockWeavix'}
    )

    ClientID: Mapped[int] = mapped_column(Integer, primary_key=True)
    LastName: Mapped[str] = mapped_column(Unicode(50, 'Cyrillic_General_CI_AS'), server_default=text("('Невідомо')"))
    FirstName: Mapped[str] = mapped_column(Unicode(50, 'Cyrillic_General_CI_AS'), server_default=text("('Невідомо')"))
    Address: Mapped[str] = mapped_column(Unicode(500, 'Cyrillic_General_CI_AS'), server_default=text("('Не вказано')"))
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime)
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime)
    MiddleName: Mapped[Optional[str]] = mapped_column(Unicode(50, 'Cyrillic_General_CI_AS'))
    Phone: Mapped[Optional[str]] = mapped_column(Unicode(15, 'Cyrillic_General_CI_AS'))
    Email: Mapped[Optional[str]] = mapped_column(Unicode(255, 'Cyrillic_General_CI_AS'))

    Orders: Mapped[List['Orders']] = relationship('Orders', back_populates='Clients_')


class Manufacturers(Base):
    __tablename__ = 'Manufacturers'
    __table_args__ = (
        PrimaryKeyConstraint('ManufacturerID', name='PK__Manufact__357E5CA10335A6E8'),
        {'schema': 'StockWeavix'}
    )

    ManufacturerID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    ManufacturerName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    ManufacturerDescription: Mapped[Optional[str]] = mapped_column(String(500, 'Cyrillic_General_CI_AS'))

    Products: Mapped[List['Products']] = relationship('Products', back_populates='Manufacturers_')


class OrderStatuses(Base):
    __tablename__ = 'OrderStatuses'
    __table_args__ = (
        PrimaryKeyConstraint('OrderStatusID', name='PK__OrderSta__BC674F4139D5CCFE'),
        {'schema': 'StockWeavix'}
    )

    OrderStatusID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    StatusName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))

    Orders: Mapped[List['Orders']] = relationship('Orders', back_populates='OrderStatuses_')


class Positions(Base):
    __tablename__ = 'Positions'
    __table_args__ = (
        PrimaryKeyConstraint('PositionID', name='PK__Position__60BB9A596E5A2324'),
        {'schema': 'StockWeavix'}
    )

    PositionID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    PositionName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))

    Employees: Mapped[List['Employees']] = relationship('Employees', back_populates='Positions_')


class ProductCategories(Base):
    __tablename__ = 'ProductCategories'
    __table_args__ = (
        PrimaryKeyConstraint('CategoryID', name='PK__ProductC__19093A2BC48B73DF'),
        {'schema': 'StockWeavix'}
    )

    CategoryID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    CategoryName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    Description: Mapped[Optional[str]] = mapped_column(String(500, 'Cyrillic_General_CI_AS'))

    Products: Mapped[List['Products']] = relationship('Products', back_populates='ProductCategories_')


class Suppliers(Base):
    __tablename__ = 'Suppliers'
    __table_args__ = (
        PrimaryKeyConstraint('SupplierID', name='PK__Supplier__4BE66694CE91E7F7'),
        {'schema': 'StockWeavix'}
    )

    SupplierID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    SupplierName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    SupplierAddress: Mapped[Optional[str]] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    SupplierPhone: Mapped[Optional[str]] = mapped_column(String(50, 'Cyrillic_General_CI_AS'))
    SupplierEDRPOU: Mapped[Optional[str]] = mapped_column(String(50, 'Cyrillic_General_CI_AS'))
    SupplierMFI: Mapped[Optional[str]] = mapped_column(String(50, 'Cyrillic_General_CI_AS'))
    ContactPerson: Mapped[Optional[str]] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))

    SupplyContracts: Mapped[List['SupplyContracts']] = relationship('SupplyContracts', back_populates='Suppliers_')


class SupplyStatuses(Base):
    __tablename__ = 'SupplyStatuses'
    __table_args__ = (
        PrimaryKeyConstraint('SupplyStatusID', name='PK__Contract__96D70656FDDE505B'),
        {'schema': 'StockWeavix'}
    )

    SupplyStatusID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    StatusName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))

    SupplyContracts: Mapped[List['SupplyContracts']] = relationship('SupplyContracts', back_populates='SupplyStatuses_')


class Warehouses(Base):
    __tablename__ = 'Warehouses'
    __table_args__ = (
        PrimaryKeyConstraint('WarehouseID', name='PK__Warehous__2608AFD922FDC967'),
        {'schema': 'StockWeavix'}
    )

    WarehouseID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    WarehouseName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    Description: Mapped[Optional[str]] = mapped_column(String(500, 'Cyrillic_General_CI_AS'))
    Address: Mapped[Optional[str]] = mapped_column(Unicode(255, 'Cyrillic_General_CI_AS'))

    Employees: Mapped[List['Employees']] = relationship('Employees', back_populates='Warehouses_')
    Zones: Mapped[List['Zones']] = relationship('Zones', back_populates='Warehouses_')
    Locations: Mapped[List['Locations']] = relationship('Locations', back_populates='Warehouses_')


t_ZoneOccupancyView = Table(
    'ZoneOccupancyView', Base.metadata,
    Column('ZoneID', Integer, nullable=False),
    Column('TotalLocations', Integer),
    Column('OccupiedLocations', Integer),
    Column('OccupancyPercentage', Float(53)),
    schema='StockWeavix'
)


class ZoneSections(Base):
    __tablename__ = 'ZoneSections'
    __table_args__ = (
        PrimaryKeyConstraint('SectionID', name='PK__ZoneSect__80EF0892ED46AC0D'),
        Index('UQ__ZoneSect__B6D6EE018FE38E67', 'SectionNumber', unique=True),
        {'schema': 'StockWeavix'}
    )

    SectionID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    SectionNumber: Mapped[int] = mapped_column(Integer)

    Locations: Mapped[List['Locations']] = relationship('Locations', back_populates='ZoneSections_')


class ZoneShelves(Base):
    __tablename__ = 'ZoneShelves'
    __table_args__ = (
        PrimaryKeyConstraint('ShelfID', name='PK__ZoneShel__DBD04F27FA0BAB71'),
        Index('UQ__ZoneShel__AFFEC82EC9B3E5AC', 'ShelfLevel', unique=True),
        {'schema': 'StockWeavix'}
    )

    ShelfID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    ShelfLevel: Mapped[int] = mapped_column(Integer)

    Locations: Mapped[List['Locations']] = relationship('Locations', back_populates='ZoneShelves_')


t_vw_LocationStatus = Table(
    'vw_LocationStatus', Base.metadata,
    Column('LocationID', Integer, nullable=False),
    Column('ZoneCode', Integer, nullable=False),
    Column('RowNumber', Integer, nullable=False),
    Column('SectionNumber', Integer, nullable=False),
    Column('ShelfLevel', Integer, nullable=False),
    Column('TotalQuantity', Integer, nullable=False),
    Column('ShelfStatus', Unicode(16, 'Cyrillic_General_CI_AS'), nullable=False),
    schema='StockWeavix'
)


class Employees(Base):
    __tablename__ = 'Employees'
    __table_args__ = (
        ForeignKeyConstraint(['PositionID'], ['StockWeavix.Positions.PositionID'], name='FK_Employees_Positions'),
        ForeignKeyConstraint(['WarehouseID'], ['StockWeavix.Warehouses.WarehouseID'], name='FK_Employees_Warehouses'),
        PrimaryKeyConstraint('EmployeeID', name='PK__Employee__7AD04FF178670A77'),
        {'schema': 'StockWeavix'}
    )

    EmployeeID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    PositionID: Mapped[int] = mapped_column(Integer)
    WarehouseID: Mapped[int] = mapped_column(Integer)
    EmployeeLastName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    EmployeeFirstName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    EmployeePatronymic: Mapped[Optional[str]] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    EmployeePassport: Mapped[Optional[str]] = mapped_column(String(50, 'Cyrillic_General_CI_AS'))
    EmployeePhone: Mapped[Optional[str]] = mapped_column(String(50, 'Cyrillic_General_CI_AS'))
    EmployeeEmail: Mapped[Optional[str]] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))

    Positions_: Mapped['Positions'] = relationship('Positions', back_populates='Employees')
    Warehouses_: Mapped['Warehouses'] = relationship('Warehouses', back_populates='Employees')


class Orders(Base):
    __tablename__ = 'Orders'
    __table_args__ = (
        ForeignKeyConstraint(['CityID'], ['StockWeavix.Cities.CityID'], name='FK_Orders_Cities'),
        ForeignKeyConstraint(['ClientID'], ['StockWeavix.Clients.ClientID'], name='FK_Orders_Clients'),
        ForeignKeyConstraint(['OrderStatusID'], ['StockWeavix.OrderStatuses.OrderStatusID'], name='FK_Orders_OrderStatuses'),
        PrimaryKeyConstraint('OrderID', name='PK_Orders_OrderID'),
        {'schema': 'StockWeavix'}
    )

    OrderID: Mapped[int] = mapped_column(Integer, primary_key=True)
    OrderDate: Mapped[datetime.date] = mapped_column(Date)
    OrderStatusID: Mapped[int] = mapped_column(Integer)
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime)
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime)
    ClientID: Mapped[Optional[int]] = mapped_column(Integer)
    CityID: Mapped[Optional[int]] = mapped_column(Integer)
    PaymentDate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    Address: Mapped[Optional[str]] = mapped_column(Unicode(255, 'Cyrillic_General_CI_AS'))
    Description: Mapped[Optional[str]] = mapped_column(Unicode(collation='Cyrillic_General_CI_AS'))

    Cities_: Mapped[Optional['Cities']] = relationship('Cities', back_populates='Orders')
    Clients_: Mapped[Optional['Clients']] = relationship('Clients', back_populates='Orders')
    OrderStatuses_: Mapped['OrderStatuses'] = relationship('OrderStatuses', back_populates='Orders')


class Products(Base):
    __tablename__ = 'Products'
    __table_args__ = (
        ForeignKeyConstraint(['ManufacturerID'], ['StockWeavix.Manufacturers.ManufacturerID'], name='FK_Products_Manufacturers'),
        ForeignKeyConstraint(['ProductCategoryID'], ['StockWeavix.ProductCategories.CategoryID'], name='FK_Products_ProductCategories'),
        PrimaryKeyConstraint('ProductID', name='PK__Products__B40CC6ED93612CFE'),
        {'schema': 'StockWeavix'}
    )

    ProductID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    ProductName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    ProductCategoryID: Mapped[int] = mapped_column(Integer)
    SKU: Mapped[str] = mapped_column(String(100, 'Cyrillic_General_CI_AS'))
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    ManufacturerID: Mapped[Optional[int]] = mapped_column(Integer)
    ProductDescription: Mapped[Optional[str]] = mapped_column(String(500, 'Cyrillic_General_CI_AS'))
    Price: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2))

    Manufacturers_: Mapped[Optional['Manufacturers']] = relationship('Manufacturers', back_populates='Products')
    ProductCategories_: Mapped['ProductCategories'] = relationship('ProductCategories', back_populates='Products')
    OrderItems: Mapped[List['OrderItems']] = relationship('OrderItems', back_populates='Products_')
    SupplyDetails: Mapped[List['SupplyDetails']] = relationship('SupplyDetails', back_populates='Products_')
    Inventory: Mapped[List['Inventory']] = relationship('Inventory', back_populates='Products_')


class SupplyContracts(Base):
    __tablename__ = 'SupplyContracts'
    __table_args__ = (
        ForeignKeyConstraint(['SupplierID'], ['StockWeavix.Suppliers.SupplierID'], name='FK_SupplyContracts_Suppliers'),
        ForeignKeyConstraint(['SupplyStatusID'], ['StockWeavix.SupplyStatuses.SupplyStatusID'], name='FK_SupplyContracts_SupplyStatuses'),
        PrimaryKeyConstraint('SupplyID', name='PK__SupplyCo__C90D3409B87C0427'),
        {'schema': 'StockWeavix'}
    )

    SupplyID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    SupplierID: Mapped[int] = mapped_column(Integer)
    SupplyStatusID: Mapped[int] = mapped_column(Integer)
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    ContractPrice: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2))
    PaymentDate: Mapped[Optional[datetime.date]] = mapped_column(Date)
    Description: Mapped[Optional[str]] = mapped_column(String(500, 'Cyrillic_General_CI_AS'))

    Suppliers_: Mapped['Suppliers'] = relationship('Suppliers', back_populates='SupplyContracts')
    SupplyStatuses_: Mapped['SupplyStatuses'] = relationship('SupplyStatuses', back_populates='SupplyContracts')
    SupplyDetails: Mapped[List['SupplyDetails']] = relationship('SupplyDetails', back_populates='SupplyContracts_')


class Zones(Base):
    __tablename__ = 'Zones'
    __table_args__ = (
        ForeignKeyConstraint(['WarehouseID'], ['StockWeavix.Warehouses.WarehouseID'], name='FK_Zones_Warehouses'),
        PrimaryKeyConstraint('ZoneID', name='PK__Zones__60166795A2BA06ED'),
        {'schema': 'StockWeavix'}
    )

    ZoneID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    ZoneCode: Mapped[int] = mapped_column(Integer)
    ZoneName: Mapped[str] = mapped_column(String(255, 'Cyrillic_General_CI_AS'))
    WarehouseID: Mapped[int] = mapped_column(Integer)
    RowMin: Mapped[int] = mapped_column(Integer)
    RowMax: Mapped[int] = mapped_column(Integer)
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))
    Description: Mapped[Optional[str]] = mapped_column(String(500, 'Cyrillic_General_CI_AS'))

    Warehouses_: Mapped['Warehouses'] = relationship('Warehouses', back_populates='Zones')
    ZoneRows: Mapped[List['ZoneRows']] = relationship('ZoneRows', back_populates='Zones_')


class OrderItems(Base):
    __tablename__ = 'OrderItems'
    __table_args__ = (
        ForeignKeyConstraint(['ProductID'], ['StockWeavix.Products.ProductID'], name='FK_OrderItems_Products'),
        PrimaryKeyConstraint('OrderItemID', name='PK__OrderIte__57ED06A11A488A57'),
        {'schema': 'StockWeavix'}
    )

    OrderItemID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    OrderID: Mapped[int] = mapped_column(Integer)
    ProductID: Mapped[int] = mapped_column(Integer)
    Quantity: Mapped[int] = mapped_column(Integer)
    UnitPrice: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2))

    Products_: Mapped['Products'] = relationship('Products', back_populates='OrderItems')


class SupplyDetails(Base):
    __tablename__ = 'SupplyDetails'
    __table_args__ = (
        ForeignKeyConstraint(['ProductID'], ['StockWeavix.Products.ProductID'], name='FK_SupplyDetails_Products'),
        ForeignKeyConstraint(['SupplyID'], ['StockWeavix.SupplyContracts.SupplyID'], name='FK_SupplyDetails_SupplyContracts'),
        PrimaryKeyConstraint('SupplyDetailID', name='PK__Contract__CCA7AF02BA495A24'),
        {'schema': 'StockWeavix'}
    )

    SupplyDetailID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    SupplyID: Mapped[int] = mapped_column(Integer)
    ProductID: Mapped[int] = mapped_column(Integer)
    Quantity: Mapped[int] = mapped_column(Integer)
    UnitPrice: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2))

    Products_: Mapped['Products'] = relationship('Products', back_populates='SupplyDetails')
    SupplyContracts_: Mapped['SupplyContracts'] = relationship('SupplyContracts', back_populates='SupplyDetails')


class ZoneRows(Base):
    __tablename__ = 'ZoneRows'
    __table_args__ = (
        ForeignKeyConstraint(['ZoneID'], ['StockWeavix.Zones.ZoneID'], name='FK_ZoneRows_Zones'),
        PrimaryKeyConstraint('ZoneRowID', name='PK__ZoneRows__A94FAD68D04FF7C1'),
        Index('UQ_ZoneRows_Zone_Row', 'ZoneID', 'RowNumber', unique=True),
        {'schema': 'StockWeavix'}
    )

    ZoneRowID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    ZoneID: Mapped[int] = mapped_column(Integer)
    RowNumber: Mapped[int] = mapped_column(Integer)

    Zones_: Mapped['Zones'] = relationship('Zones', back_populates='ZoneRows')
    Locations: Mapped[List['Locations']] = relationship('Locations', back_populates='ZoneRows_')


class Locations(Base):
    __tablename__ = 'Locations'
    __table_args__ = (
        ForeignKeyConstraint(['SectionID'], ['StockWeavix.ZoneSections.SectionID'], name='FK_Locations_ZoneSection'),
        ForeignKeyConstraint(['ShelfID'], ['StockWeavix.ZoneShelves.ShelfID'], name='FK_Locations_ZoneShelf'),
        ForeignKeyConstraint(['WarehouseID'], ['StockWeavix.Warehouses.WarehouseID'], name='FK_Locations_Warehouse'),
        ForeignKeyConstraint(['ZoneRowID'], ['StockWeavix.ZoneRows.ZoneRowID'], name='FK_Locations_ZoneRow'),
        PrimaryKeyConstraint('LocationID', name='PK__Location__E7FEA477C0CF483D'),
        {'schema': 'StockWeavix'}
    )

    LocationID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    CreatedDate: Mapped[datetime.datetime] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    LastUpdatedDate: Mapped[datetime.datetime] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    WarehouseID: Mapped[Optional[int]] = mapped_column(Integer)
    ZoneRowID: Mapped[Optional[int]] = mapped_column(Integer)
    SectionID: Mapped[Optional[int]] = mapped_column(Integer)
    ShelfID: Mapped[Optional[int]] = mapped_column(Integer)

    ZoneSections_: Mapped[Optional['ZoneSections']] = relationship('ZoneSections', back_populates='Locations')
    ZoneShelves_: Mapped[Optional['ZoneShelves']] = relationship('ZoneShelves', back_populates='Locations')
    Warehouses_: Mapped[Optional['Warehouses']] = relationship('Warehouses', back_populates='Locations')
    ZoneRows_: Mapped[Optional['ZoneRows']] = relationship('ZoneRows', back_populates='Locations')
    Inventory: Mapped[List['Inventory']] = relationship('Inventory', back_populates='Locations_')


class Inventory(Base):
    __tablename__ = 'Inventory'
    __table_args__ = (
        ForeignKeyConstraint(['LocationID'], ['StockWeavix.Locations.LocationID'], name='FK_Inventory_Locations'),
        ForeignKeyConstraint(['ProductID'], ['StockWeavix.Products.ProductID'], name='FK_Inventory_Products'),
        PrimaryKeyConstraint('InventoryID', name='PK__Inventor__F5FDE6D3B1869395'),
        {'schema': 'StockWeavix'}
    )

    InventoryID: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    ProductID: Mapped[int] = mapped_column(Integer)
    LocationID: Mapped[int] = mapped_column(Integer)
    Quantity: Mapped[int] = mapped_column(Integer)
    LastUpdated: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('(getdate())'))

    Locations_: Mapped['Locations'] = relationship('Locations', back_populates='Inventory')
    Products_: Mapped['Products'] = relationship('Products', back_populates='Inventory')
