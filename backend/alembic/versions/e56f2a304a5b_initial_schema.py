"""Initial schema

Revision ID: e56f2a304a5b
Revises: 
Create Date: 2026-06-05 11:27:25.176555

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e56f2a304a5b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'accounts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('account_number', sa.String(), nullable=True),
        sa.Column('registered_name', sa.String(), nullable=True),
        sa.Column('account_type', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('ifsc_code', sa.String(), nullable=True),
        sa.Column('upi_id', sa.String(), nullable=True),
        sa.Column('balance', sa.Float(), nullable=True),
        sa.Column('is_flagged', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_account_number'), 'accounts', ['account_number'], unique=True)
    op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)
    op.create_index(op.f('ix_accounts_registered_name'), 'accounts', ['registered_name'], unique=False)
    op.create_index(op.f('ix_accounts_state'), 'accounts', ['state'], unique=False)

    op.create_table(
        'transactions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('transaction_ref', sa.String(), nullable=True),
        sa.Column('source_account_id', sa.String(), nullable=True),
        sa.Column('target_account_id', sa.String(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('transaction_type', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_flag', sa.String(), nullable=True),
        sa.Column('metadata_blob', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_ref'), 'transactions', ['transaction_ref'], unique=True)
    op.create_index(op.f('ix_transactions_source_account_id'), 'transactions', ['source_account_id'], unique=False)
    op.create_index(op.f('ix_transactions_target_account_id'), 'transactions', ['target_account_id'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_type'), 'transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_transactions_risk_flag'), 'transactions', ['risk_flag'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_transactions_risk_flag'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_transaction_type'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_target_account_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_source_account_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_transaction_ref'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')

    op.drop_index(op.f('ix_accounts_state'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_registered_name'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_id'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_account_number'), table_name='accounts')
    op.drop_table('accounts')
