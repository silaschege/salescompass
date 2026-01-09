import logging
from typing import List, Dict, Any, Optional, Union
import psycopg2
from psycopg2.extras import Json
from pgvector.psycopg2 import register_vector
import numpy as np
from ml_models.infrastructure.config.settings import config

class VectorDatabase:
    """
    Interface for Vector Database operations using PostgreSQL + pgvector.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        self.conn_str = connection_string or config.vector_db_url
        self.logger = logging.getLogger(__name__)
        self._conn = None
        
    def _get_connection(self):
        """Get or create database connection with pgvector type registration"""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(self.conn_str)
                # Enable pgvector extension support
                with self._conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    self._conn.commit()
                register_vector(self._conn)
            except Exception as e:
                self.logger.error(f"Failed to connect to Vector DB: {str(e)}")
                raise
        return self._conn

    def create_table(self, table_name: str, dim: int):
        """Create a table for storing embeddings if it doesn't exist"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id VARCHAR(255) PRIMARY KEY,
                        embedding vector({dim}),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx 
                    ON {table_name} USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
            conn.commit()
            self.logger.info(f"Table {table_name} ready.")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error creating table {table_name}: {str(e)}")
            raise

    def upsert_embedding(self, table_name: str, item_id: str, embedding: List[float], metadata: Dict[str, Any] = None):
        """Insert or update an embedding"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {table_name} (id, embedding, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata;
                """, (item_id, embedding, Json(metadata or {})))
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error upserting embedding for {item_id}: {str(e)}")
            raise

    def search_similar(self, table_name: str, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar items using cosine similarity"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT id, metadata, 1 - (embedding <=> %s) as similarity
                    FROM {table_name}
                    ORDER BY embedding <=> %s
                    LIMIT %s;
                """, (embedding, embedding, limit))
                results = cur.fetchall()
                
            return [
                {"id": r[0], "metadata": r[1], "similarity": float(r[2])}
                for r in results
            ]
        except Exception as e:
            self.logger.error(f"Error searching similar items: {str(e)}")
            return []

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
