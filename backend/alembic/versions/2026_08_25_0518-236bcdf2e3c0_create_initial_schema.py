"""create_initial_schema

Revision ID: 236bcdf2e3c0
Revises: 
Create Date: 2026-08-25 05:18:58.891746+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '236bcdf2e3c0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Products Table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku_code', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('unit_cost', sa.Float(), nullable=False),
        sa.Column('lead_time_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_sku_code'), 'products', ['sku_code'], unique=True)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)

    # 2. Stores Table
    op.create_table(
        'stores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_stores_id'), 'stores', ['id'], unique=False)
    op.create_index(op.f('ix_stores_city'), 'stores', ['city'], unique=False)
    op.create_index(op.f('ix_stores_region'), 'stores', ['region'], unique=False)

    # 3. Promotions Table
    op.create_table(
        'promotions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('discount_pct', sa.Float(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_promotions_id'), 'promotions', ['id'], unique=False)
    op.create_index(op.f('ix_promotions_start_date'), 'promotions', ['start_date'], unique=False)
    op.create_index(op.f('ix_promotions_end_date'), 'promotions', ['end_date'], unique=False)
    op.create_index(op.f('ix_promotions_product_id'), 'promotions', ['product_id'], unique=False)
    op.create_index(op.f('ix_promotions_category'), 'promotions', ['category'], unique=False)

    # 4. Sales Table
    op.create_table(
        'sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('units_sold', sa.Integer(), nullable=False),
        sa.Column('revenue', sa.Float(), nullable=False),
        sa.Column('promotion_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['promotion_id'], ['promotions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'store_id', 'date', name='uq_sales_product_store_date'),
    )
    op.create_index(op.f('ix_sales_id'), 'sales', ['id'], unique=False)
    op.create_index(op.f('ix_sales_date'), 'sales', ['date'], unique=False)
    op.create_index(op.f('ix_sales_product_id'), 'sales', ['product_id'], unique=False)
    op.create_index(op.f('ix_sales_store_id'), 'sales', ['store_id'], unique=False)
    op.create_index(op.f('ix_sales_promotion_id'), 'sales', ['promotion_id'], unique=False)
    op.create_index('ix_sales_store_product_date', 'sales', ['store_id', 'product_id', 'date'], unique=False)

    # 5. Inventories Table
    op.create_table(
        'inventories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('current_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reorder_point', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('safety_stock', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'store_id', name='uq_inventory_product_store'),
    )
    op.create_index(op.f('ix_inventories_id'), 'inventories', ['id'], unique=False)
    op.create_index(op.f('ix_inventories_product_id'), 'inventories', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventories_store_id'), 'inventories', ['store_id'], unique=False)

    # 6. Forecast Results Table
    op.create_table(
        'forecast_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('predicted_units', sa.Float(), nullable=False),
        sa.Column('lower_bound', sa.Float(), nullable=False),
        sa.Column('upper_bound', sa.Float(), nullable=False),
        sa.Column('model_used', sa.String(length=50), nullable=False, server_default='lightgbm'),
        sa.Column('mape', sa.Float(), nullable=True),
        sa.Column('rmse', sa.Float(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_forecast_results_id'), 'forecast_results', ['id'], unique=False)
    op.create_index(op.f('ix_forecast_results_product_id'), 'forecast_results', ['product_id'], unique=False)
    op.create_index(op.f('ix_forecast_results_store_id'), 'forecast_results', ['store_id'], unique=False)
    op.create_index(op.f('ix_forecast_results_forecast_date'), 'forecast_results', ['forecast_date'], unique=False)
    op.create_index('ix_forecast_prod_store_date', 'forecast_results', ['product_id', 'store_id', 'forecast_date'], unique=False)

    # 7. Alerts Table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('store_id', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='new'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)
    op.create_index(op.f('ix_alerts_type'), 'alerts', ['type'], unique=False)
    op.create_index(op.f('ix_alerts_severity'), 'alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_alerts_status'), 'alerts', ['status'], unique=False)
    op.create_index(op.f('ix_alerts_product_id'), 'alerts', ['product_id'], unique=False)
    op.create_index(op.f('ix_alerts_store_id'), 'alerts', ['store_id'], unique=False)
    op.create_index('ix_alerts_status_severity', 'alerts', ['status', 'severity'], unique=False)

    # 8. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='planner'),
        sa.Column('assigned_store_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assigned_store_id'], ['stores.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_assigned_store_id'), 'users', ['assigned_store_id'], unique=False)

    # 9. Weekly Sales Summaries Table
    op.create_table(
        'weekly_sales_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('total_units_sold', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_revenue', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('last_aggregated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'store_id', 'year', 'week_number', name='uq_weekly_summary_item'),
    )
    op.create_index(op.f('ix_weekly_sales_summaries_id'), 'weekly_sales_summaries', ['id'], unique=False)
    op.create_index(op.f('ix_weekly_sales_summaries_product_id'), 'weekly_sales_summaries', ['product_id'], unique=False)
    op.create_index(op.f('ix_weekly_sales_summaries_store_id'), 'weekly_sales_summaries', ['store_id'], unique=False)
    op.create_index(op.f('ix_weekly_sales_summaries_year'), 'weekly_sales_summaries', ['year'], unique=False)
    op.create_index(op.f('ix_weekly_sales_summaries_week_number'), 'weekly_sales_summaries', ['week_number'], unique=False)
    op.create_index('ix_weekly_summary_store_prod_year_week', 'weekly_sales_summaries', ['store_id', 'product_id', 'year', 'week_number'], unique=False)


def downgrade() -> None:
    op.drop_table('weekly_sales_summaries')
    op.drop_table('users')
    op.drop_table('alerts')
    op.drop_table('forecast_results')
    op.drop_table('inventories')
    op.drop_table('sales')
    op.drop_table('promotions')
    op.drop_table('stores')
    op.drop_table('products')
