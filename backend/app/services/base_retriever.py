from abc import ABC, abstractmethod

class RetrievalResult:
    """
    Standardized data transfer object representing a single retrieved text chunk match.
    Provides uniform keys and guarantees schema alignment between semantic, BM25, and hybrid retrievers.
    """
    def __init__(
        self,
        rank: int,
        score: float,
        retrieval_type: str,
        document_id: str,
        document_name: str,
        page_number: int,
        chunk_id: str,
        text: str,
        match_source: str = None,
        rerank_score: float = None
    ):
        self.rank = rank
        self.score = score
        self.similarity_score = score  # For backwards compatibility with the original semantic search key
        self.retrieval_type = retrieval_type
        self.document_id = document_id
        self.document_name = document_name
        self.page_number = page_number
        self.chunk_id = chunk_id
        self.text = text
        self.match_source = match_source
        self.rerank_score = rerank_score

    def to_dict(self) -> dict:
        """Converts the result model into a standard JSON-serializable dictionary."""
        return {
            "rank": self.rank,
            "score": self.score,
            "similarity_score": self.similarity_score,
            "retrieval_type": self.retrieval_type,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page_number": self.page_number,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "match_source": self.match_source,
            "rerank_score": self.rerank_score
        }

class BaseRetriever(ABC):
    """
    Abstract base class interface defining the requirements for RAG retrievers.
    This enables uniform interaction with semantic and sparse retrieval modules.
    """
    @abstractmethod
    def search(self, query: str, top_k: int = None) -> list[RetrievalResult]:
        """
        Executes a search query and returns a ranked list of RetrievalResult models.
        
        Args:
            query (str): The search query.
            top_k (int, optional): The number of matching chunks to retrieve.
            
        Returns:
            list[RetrievalResult]: Sorted, ranked list of matches.
        """
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """
        Returns stats about the retriever or underlying index.
        
        Returns:
            dict: Statistical metadata (e.g. document count, chunk count, model used).
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Runs a health check on the retriever or index to verify functionality.
        
        Returns:
            bool: True if healthy and ready to serve queries, False otherwise.
        """
        pass
