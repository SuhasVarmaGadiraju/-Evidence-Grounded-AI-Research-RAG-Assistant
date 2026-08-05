"""Add conversation memory tables (research_sessions, messages, retrieval_logs)

Revision ID: 0002_add_conversation_memory
Revises: 0001_create_initial_tables
Create Date: 2026-08-05 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_conversation_memory'
down_revision = '0001_create_initial_tables'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create 'research_sessions' table
    op.create_table(
        'research_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_uuid', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), server_default='New Research Session', nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_sessions_session_uuid'), 'research_sessions', ['session_uuid'], unique=True)
    op.create_index(op.f('ix_research_sessions_user_id'), 'research_sessions', ['user_id'], unique=False)

    # 2. Create 'messages' table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_uuid', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='user', nullable=False),
        sa.Column('user_question', sa.Text(), nullable=True),
        sa.Column('assistant_answer', sa.Text(), nullable=True),
        sa.Column('latency', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('token_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_message_uuid'), 'messages', ['message_uuid'], unique=True)
    op.create_index(op.f('ix_messages_session_id'), 'messages', ['session_id'], unique=False)

    # 3. Create 'retrieval_logs' table
    op.create_table(
        'retrieval_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('document_uuid', sa.String(length=36), nullable=False),
        sa.Column('chunk_uuid', sa.String(length=255), nullable=False),
        sa.Column('page_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('faiss_vector_id', sa.BigInteger(), nullable=True),
        sa.Column('semantic_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('bm25_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('rrf_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('reranker_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('retrieval_strategy', sa.String(length=50), server_default='Hybrid RRF', nullable=False),
        sa.Column('retrieval_rank', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_retrieval_logs_message_id'), 'retrieval_logs', ['message_id'], unique=False)
    op.create_index(op.f('ix_retrieval_logs_document_uuid'), 'retrieval_logs', ['document_uuid'], unique=False)
    op.create_index(op.f('ix_retrieval_logs_chunk_uuid'), 'retrieval_logs', ['chunk_uuid'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_retrieval_logs_chunk_uuid'), table_name='retrieval_logs')
    op.drop_index(op.f('ix_retrieval_logs_document_uuid'), table_name='retrieval_logs')
    op.drop_index(op.f('ix_retrieval_logs_message_id'), table_name='retrieval_logs')
    op.drop_table('retrieval_logs')

    op.drop_index(op.f('ix_messages_session_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_message_uuid'), table_name='messages')
    op.drop_table('messages')

    op.drop_index(op.f('ix_research_sessions_user_id'), table_name='research_sessions')
    op.drop_index(op.f('ix_research_sessions_session_uuid'), table_name='research_sessions')
    op.drop_table('research_sessions')
