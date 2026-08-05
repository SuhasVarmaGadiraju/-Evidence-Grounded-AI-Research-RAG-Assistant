import sys
import os
import io
import uuid
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from database.database import db
from database.models.user import User
from database.models.document import Document
from database.models.chunk import Chunk
from app.services.user_service import sync_user_profile

class TestPostgreSQLIntegration(unittest.TestCase):
    def setUp(self):
        os.environ["FLASK_ENV"] = "testing"
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.rollback()
            db.session.remove()

    def test_user_synchronization(self):
        """Verify user profile sync creates and updates records without duplicates."""
        with self.app.app_context():
            test_uid = f"test_firebase_{uuid.uuid4().hex[:8]}"
            test_email = f"user_{uuid.uuid4().hex[:6]}@example.com"

            # 1. Sync new user
            user1 = sync_user_profile({
                "firebase_uid": test_uid,
                "email": test_email,
                "name": "Initial Name",
                "provider": "google.com"
            })
            self.assertIsNotNone(user1.id)
            self.assertEqual(user1.email, test_email)
            self.assertEqual(user1.name, "Initial Name")

            user_count_before = User.query.count()

            # 2. Sync existing user with updated info
            user2 = sync_user_profile({
                "firebase_uid": test_uid,
                "email": test_email,
                "name": "Updated Name",
                "photo_url": "https://example.com/avatar.png",
                "provider": "google.com"
            })
            user_count_after = User.query.count()

            self.assertEqual(user1.id, user2.id)
            self.assertEqual(user_count_before, user_count_after)
            self.assertEqual(user2.name, "Updated Name")
            self.assertEqual(user2.photo_url, "https://example.com/avatar.png")

    def test_user_sync_api_endpoint(self):
        """Verify POST /api/users/sync API route."""
        test_uid = f"uid_api_{uuid.uuid4().hex[:8]}"
        test_email = f"api_user_{uuid.uuid4().hex[:6]}@example.com"

        response = self.client.post("/api/users/sync", json={
            "firebase_uid": test_uid,
            "email": test_email,
            "name": "API Test User",
            "provider": "password"
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["email"], test_email)

    def test_ingestion_and_postgres_persistence(self):
        """Verify PDF ingestion creates Document and Chunk rows with FAISS vector ID sync."""
        with self.app.app_context():
            # Create test user
            user = User(
                firebase_uid=f"uid_ingest_{uuid.uuid4().hex[:6]}",
                email=f"ingest_{uuid.uuid4().hex[:6]}@example.com",
                name="Ingest Tester"
            )
            db.session.add(user)
            db.session.commit()

            # Simulate PDF upload
            pdf_bytes = b"%PDF-1.4 Mock PDF content for testing ingestion pipeline persistence into PostgreSQL."
            data = {
                "files": (io.BytesIO(pdf_bytes), "test_document.pdf")
            }
            headers = {
                "X-User-UID": user.firebase_uid,
                "X-User-Email": user.email
            }

            with patch("app.services.ingest.PdfReader") as mock_pdf_reader, \
                 patch("app.services.embedding_generator.generate_embeddings_for_document") as mock_gen_emb, \
                 patch("app.services.vector_index.get_vector_index_service") as mock_get_index_service:

                # Mock PDF page text
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "This is sample text extracted from page one of test document."
                mock_reader_inst = MagicMock()
                mock_reader_inst.pages = [mock_page]
                mock_pdf_reader.return_value = mock_reader_inst

                # Mock embeddings return
                mock_gen_emb.return_value = {
                    "embedding_model": "all-MiniLM-L6-v2",
                    "embedding_dimension": 384
                }

                # Mock FAISS index service
                mock_index_service = MagicMock()
                mock_get_index_service.return_value = mock_index_service

                response = self.client.post("/api/upload", data=data, headers=headers, content_type="multipart/form-data")
                self.assertEqual(response.status_code, 200)

                res_data = response.get_json()
                self.assertTrue(res_data["success"])
                doc_id = res_data["results"][0]["document_id"]

                # Verify Document persisted in PostgreSQL
                doc = Document.query.filter_by(document_uuid=doc_id).first()
                self.assertIsNotNone(doc)
                self.assertEqual(doc.title, "test_document.pdf")
                self.assertEqual(doc.status, "Completed")
                self.assertGreaterEqual(doc.chunk_count, 1)

                # Verify Chunks persisted in PostgreSQL
                chunks = Chunk.query.filter_by(document_id=doc.id).all()
                self.assertGreaterEqual(len(chunks), 1)
                self.assertEqual(chunks[0].document_id, doc.id)

    def test_get_documents_api_reads_from_postgres(self):
        """Verify GET /api/documents queries PostgreSQL."""
        with self.app.app_context():
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                document_uuid=doc_uuid,
                title="sample_library.pdf",
                filename=f"{doc_uuid}_sample_library.pdf",
                filepath=f"/data/raw/{doc_uuid}_sample_library.pdf",
                pages=5,
                file_size=1024,
                status="Completed",
                chunk_count=3,
                embedding_count=3
            )
            db.session.add(doc)
            db.session.commit()

            response = self.client.get("/api/documents")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data["success"])

            found_docs = [d for d in data["documents"] if d["document_id"] == doc_uuid]
            self.assertEqual(len(found_docs), 1)
            self.assertEqual(found_docs[0]["original_filename"], "sample_library.pdf")

    def test_get_chunks_api_reads_from_postgres(self):
        """Verify GET /api/documents/<doc_id>/chunks queries PostgreSQL chunks table."""
        with self.app.app_context():
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                document_uuid=doc_uuid,
                title="chunk_test.pdf",
                filename=f"{doc_uuid}_chunk_test.pdf",
                filepath="/tmp/test.pdf",
                status="Completed"
            )
            db.session.add(doc)
            db.session.commit()

            chunk = Chunk(
                chunk_uuid=str(uuid.uuid4()),
                document_id=doc.id,
                page_number=1,
                chunk_index=0,
                text="This is a test chunk from PostgreSQL",
                faiss_vector_id=42
            )
            db.session.add(chunk)
            db.session.commit()

            response = self.client.get(f"/api/documents/{doc_uuid}/chunks?limit=5")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["total_chunks"], 1)
            self.assertEqual(data["chunks"][0]["text"], "This is a test chunk from PostgreSQL")
            self.assertEqual(data["chunks"][0]["faiss_vector_id"], 42)

    def test_rename_and_delete_workflow(self):
        """Verify PATCH rename and DELETE cascade document removal in PostgreSQL."""
        with self.app.app_context():
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                document_uuid=doc_uuid,
                title="old_name.pdf",
                filename=f"{doc_uuid}_old_name.pdf",
                filepath="/tmp/old.pdf",
                status="Completed"
            )
            db.session.add(doc)
            db.session.commit()

            chunk = Chunk(
                chunk_uuid=str(uuid.uuid4()),
                document_id=doc.id,
                page_number=1,
                chunk_index=0,
                text="Chunk text for deletion test"
            )
            db.session.add(chunk)
            db.session.commit()

            # 1. Rename document
            rename_res = self.client.patch(f"/api/documents/{doc_uuid}", json={"filename": "new_name.pdf"})
            self.assertEqual(rename_res.status_code, 200)
            renamed_doc = Document.query.filter_by(document_uuid=doc_uuid).first()
            self.assertEqual(renamed_doc.title, "new_name.pdf")

            # 2. Delete document
            with patch("app.services.vector_index.get_vector_index_service") as mock_get_index:
                mock_index_service = MagicMock()
                mock_get_index.return_value = mock_index_service

                delete_res = self.client.delete(f"/api/documents/{doc_uuid}")
                self.assertEqual(delete_res.status_code, 200)

                # Confirm Document and Chunk deleted from PostgreSQL
                deleted_doc = Document.query.filter_by(document_uuid=doc_uuid).first()
                self.assertIsNone(deleted_doc)
                deleted_chunks = Chunk.query.filter_by(document_id=doc.id).all()
                self.assertEqual(len(deleted_chunks), 0)

if __name__ == "__main__":
    unittest.main()
