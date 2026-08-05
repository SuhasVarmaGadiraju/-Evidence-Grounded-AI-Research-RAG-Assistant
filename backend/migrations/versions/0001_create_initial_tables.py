"""Create initial tables (users, documents, chunks)

Revision ID: 0001_create_initial_tables
Revises: 
Create Date: 2026-08-05 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_initial_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create 'users' table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('firebase_uid', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('photo_url', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_firebase_uid'), 'users', ['firebase_uid'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Create 'documents' table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_uuid', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('filepath', sa.String(length=512), nullable=False),
        sa.Column('pages', sa.Integer(), server_default='0', nullable=False),
        sa.Column('file_size', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Queued', nullable=False),
        sa.Column('chunk_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('embedding_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_document_uuid'), 'documents', ['document_uuid'], unique=True)
    op.create_index(op.f('ix_documents_uploaded_by'), 'documents', ['uploaded_by'], unique=False)

    # 3. Create 'chunks' table
    op.create_table(
        'chunks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chunk_uuid', sa.String(length=255), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('faiss_vector_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chunks_chunk_uuid'), 'chunks', ['chunk_uuid'], unique=True)
    op.create_index(op.f('ix_chunks_document_id'), 'chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_chunks_faiss_vector_id'), 'chunks', ['faiss_vector_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_chunks_faiss_vector_id'), table_name='chunks')
    op.drop_index(op.f('ix_chunks_document_id'), table_name='chunks')
    op.drop_index(op.f('ix_chunks_chunk_uuid'), table_name='chunks')
    op.drop_table('chunks')

    op.drop_index(op.f('ix_documents_uploaded_by'), table_name='documents')
    op.drop_index(op.f('ix_documents_document_uuid'), table_name='documents')
    op.drop_table('documents')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_firebase_uid'), table_name='users')
    op.drop_table('users')
