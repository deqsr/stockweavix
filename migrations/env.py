import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# Імпортуємо ваш db об'єкт з Flask-SQLAlchemy
from app.models import db  # Переконайтеся, що цей шлях правильний!

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# add your model's MetaData object here
# for 'autogenerate' support
config.set_main_option('sqlalchemy.url', get_engine_url())

# Використовуємо метадані з вашого db об'єкта
target_metadata = db.metadata


# Функція для фільтрації об'єктів під час автогенерації
def include_object(object, name, type_, reflected, compare_to):
    # Якщо об'єкт - це таблиця (type_ == "table") І має маркер 'is_view': True в info,
    # то НЕ включаємо його в автогенерацію.
    if type_ == "table" and object.info.get("is_view", False):
        logger.info(f"Ignoring view-like table in autogenerate: {name}")
        return False

    # Якщо об'єкт - це індекс, І він належить до таблиці, яка є view,
    # то також НЕ включаємо його. Це важливо, бо для view, визначеної
    # як модель з primary_key, Alembic може спробувати створити індекс.
    if type_ == "index" and hasattr(object, 'table') and object.table is not None and object.table.info.get("is_view",
                                                                                                            False):
        logger.info(f"Ignoring index on view-like table in autogenerate: {name} on {object.table.name}")
        return False

    # Для всіх інших об'єктів повертаємо True (включаємо в автогенерацію)
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=target_metadata.schema,
        include_schemas=True,
        include_object=include_object  # <--- ДОДАНО ФІЛЬТР
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = {}
    if hasattr(current_app.extensions['migrate'], 'configure_args'):
        conf_args = current_app.extensions['migrate'].configure_args

    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    if 'version_table_schema' not in conf_args:
        conf_args['version_table_schema'] = target_metadata.schema
    if 'include_schemas' not in conf_args:
        conf_args['include_schemas'] = True
    if 'include_object' not in conf_args:  # <--- ДОДАНО
        conf_args['include_object'] = include_object  # <--- ДОДАНО

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()