"""add_findings_and_iteration_tracking

Revision ID: add_findings_iter_001
Revises: 4ae3ce5535a2
Create Date: 2026-02-06 13:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_findings_iter_001'
down_revision = '4ae3ce5535a2'  # Latest revision from initial schema
depends_on = None


def upgrade():
    # Create findings table
    op.create_table(
        'findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('finding_id', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('uploaded_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('iteration_number', sa.Integer(), default=0, nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), default='active', nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('error_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('regulation_ref', sa.String(255), nullable=True),
        sa.Column('element_id', sa.String(255), nullable=True),
        sa.Column('critique_trail', postgresql.JSONB, default=list, nullable=False),
        sa.Column('meta', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for findings
    op.create_index('idx_finding_document', 'findings', ['document_id'])
    op.create_index('idx_finding_iteration', 'findings', ['document_id', 'iteration_number'])
    op.create_index('idx_finding_status', 'findings', ['status'])
    op.create_index('idx_finding_confidence', 'findings', ['confidence_score'])
    
    # Add iteration tracking columns to uploaded_documents
    op.add_column('uploaded_documents', sa.Column('iteration_count', sa.Integer(), default=0, nullable=False, server_default='0'))
    op.add_column('uploaded_documents', sa.Column('parent_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('uploaded_documents.id'), nullable=True))
    op.add_column('uploaded_documents', sa.Column('iteration_history', postgresql.JSONB, default=list, nullable=False, server_default='[]'))


def downgrade():
    # Remove iteration tracking columns from uploaded_documents
    op.drop_column('uploaded_documents', 'iteration_history')
    op.drop_column('uploaded_documents', 'parent_document_id')
    op.drop_column('uploaded_documents', 'iteration_count')
    
    # Drop indexes for findings
    op.drop_index('idx_finding_confidence', 'findings')
    op.drop_index('idx_finding_status', 'findings')
    op.drop_index('idx_finding_iteration', 'findings')
    op.drop_index('idx_finding_document', 'findings')
    
    # Drop findings table
    op.drop_table('findings')
