import os
import json
import logging
import re
import numpy as np

logger = logging.getLogger("rag_backend.chunker")

from app.services.embedding import EmbeddingService

def split_text_recursive(text, separators, chunk_size, overlap):
    """
    Helper function to recursively split text by priority separators,
    collapsing elements together up to chunk_size characters with overlap backtracking.
    """
    if len(text) <= chunk_size:
        return [text]
        
    if not separators:
        # Base character slicing fallback
        chunks = []
        start = 0
        step = chunk_size - overlap
        if step <= 0:
            step = chunk_size
        while start < len(text):
            chunks.append(text[start:start+chunk_size])
            start += step
        return chunks

    separator = separators[0]
    next_separators = separators[1:]
    
    parts = text.split(separator)
    
    final_chunks = []
    current_chunk_parts = []
    current_len = 0
    
    for part in parts:
        if len(part) > chunk_size:
            if current_chunk_parts:
                final_chunks.append(separator.join(current_chunk_parts))
                current_chunk_parts = []
                current_len = 0
            sub_chunks = split_text_recursive(part, next_separators, chunk_size, overlap)
            final_chunks.extend(sub_chunks)
        else:
            separator_len = len(separator) if current_chunk_parts else 0
            if current_len + separator_len + len(part) <= chunk_size:
                current_chunk_parts.append(part)
                current_len += separator_len + len(part)
            else:
                if current_chunk_parts:
                    final_chunks.append(separator.join(current_chunk_parts))
                
                # Backtrack to satisfy overlap boundary
                backtrack_parts = []
                backtrack_len = 0
                for p in reversed(current_chunk_parts):
                    sep_l = len(separator) if backtrack_parts else 0
                    if backtrack_len + sep_l + len(p) <= overlap:
                        backtrack_parts.insert(0, p)
                        backtrack_len += sep_l + len(p)
                    else:
                        break
                        
                current_chunk_parts = backtrack_parts + [part]
                current_len = backtrack_len + (len(separator) if backtrack_parts else 0) + len(part)
                
    if current_chunk_parts:
        final_chunks.append(separator.join(current_chunk_parts))
        
    return final_chunks

def chunk_text_semantic(text, doc_id, page_number, chunk_size=500, overlap=100, threshold=0.6):
    """
    Split text into sentences, encode them, calculate similarities between consecutive sentences,
    and create a boundary whenever similarity falls below the threshold or max chunk size is exceeded.
    """
    # 1. Tokenize into sentences using regex lookbehind
    sentence_splits = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentence_splits if s.strip()]
    
    if not sentences:
        return []
        
    if len(sentences) == 1:
        return [{
            "chunk_id": f"{doc_id}_p{page_number}_c0",
            "document_id": doc_id,
            "page_number": page_number,
            "chunk_index": 0,
            "text": sentences[0],
            "char_count": len(sentences[0]),
            "strategy": "semantic"
        }]
        
    # 2. Generate embeddings for sentences
    embedding_service = EmbeddingService()
    embeddings = embedding_service.embed_batch(sentences)
    
    # 3. Calculate cosine similarities between consecutive sentences
    similarities = []
    for i in range(len(sentences) - 1):
        u = embeddings[i]
        v = embeddings[i + 1]
        norm_u = np.linalg.norm(u)
        norm_v = np.linalg.norm(v)
        
        if norm_u == 0 or norm_v == 0:
            sim = 0.0
        else:
            sim = np.dot(u, v) / (norm_u * norm_v)
        similarities.append(float(sim))
        
    # 4. Group sentences into semantic chunks
    chunks = []
    current_sentences = [sentences[0]]
    current_len = len(sentences[0])
    chunk_idx = 0
    
    for i in range(len(sentences) - 1):
        next_sentence = sentences[i + 1]
        similarity = similarities[i]
        
        # Check boundary rules:
        # a. Exceeds max character limit
        exceeds_limit = (current_len + 1 + len(next_sentence)) > chunk_size
        # b. Similarity falls below the threshold
        below_threshold = similarity < threshold
        
        if exceeds_limit or below_threshold:
            # Save the current chunk
            chunk_text = " ".join(current_sentences)
            if len(chunk_text.strip()) >= 5:
                chunks.append({
                    "chunk_id": f"{doc_id}_p{page_number}_c{chunk_idx}",
                    "document_id": doc_id,
                    "page_number": page_number,
                    "chunk_index": chunk_idx,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "strategy": "semantic"
                })
                chunk_idx += 1
                
            # Backtrack sentence grouping for overlap support
            backtrack_sentences = []
            backtrack_len = 0
            for s in reversed(current_sentences):
                space_l = 1 if backtrack_sentences else 0
                if backtrack_len + space_l + len(s) <= overlap:
                    backtrack_sentences.insert(0, s)
                    backtrack_len += space_l + len(s)
                else:
                    break
                    
            current_sentences = backtrack_sentences + [next_sentence]
            current_len = backtrack_len + (1 if backtrack_sentences else 0) + len(next_sentence)
        else:
            # Merge into current chunk group
            current_sentences.append(next_sentence)
            current_len += 1 + len(next_sentence)
            
    # Save remaining final chunk
    if current_sentences:
        chunk_text = " ".join(current_sentences)
        if len(chunk_text.strip()) >= 5:
            chunks.append({
                "chunk_id": f"{doc_id}_p{page_number}_c{chunk_idx}",
                "document_id": doc_id,
                "page_number": page_number,
                "chunk_index": chunk_idx,
                "text": chunk_text,
                "char_count": len(chunk_text),
                "strategy": "semantic"
            })
            
    return chunks

def chunk_page_text(cleaned_text, doc_id, page_number, chunk_size=500, overlap=100, strategy="fixed_character", threshold=0.6):
    """
    Unified entry point routing to character-slicing (fixed),
    separator-splitting (recursive), or embedding similarity (semantic) chunking.
    """
    if not cleaned_text or len(cleaned_text.strip()) == 0:
        return []
        
    if strategy == "semantic":
        logger.info(f"Using semantic text chunking on page {page_number} (threshold: {threshold})")
        return chunk_text_semantic(cleaned_text, doc_id, page_number, chunk_size, overlap, threshold)
        
    elif strategy == "recursive":
        logger.info(f"Using recursive text chunking on page {page_number}")
        separators = ["\n\n", ". ", "? ", "! ", "\n", " ", ""]
        text_segments = split_text_recursive(cleaned_text, separators, chunk_size, overlap)
        
        chunks = []
        for idx, segment in enumerate(text_segments):
            chunk_content = segment.strip()
            if len(chunk_content) >= 5:
                chunks.append({
                    "chunk_id": f"{doc_id}_p{page_number}_c{idx}",
                    "document_id": doc_id,
                    "page_number": page_number,
                    "chunk_index": idx,
                    "text": chunk_content,
                    "char_count": len(chunk_content),
                    "strategy": "recursive"
                })
        return chunks
        
    else:
        # Fallback / Default: fixed_character sliding window slicing
        logger.info(f"Using fixed character chunking on page {page_number}")
        chunks = []
        text_len = len(cleaned_text)
        step = chunk_size - overlap
        if step <= 0:
            step = chunk_size
            
        start = 0
        idx = 0
        while start < text_len:
            end = start + chunk_size
            chunk_content = cleaned_text[start:end].strip()
            
            if len(chunk_content) >= 5:
                chunks.append({
                    "chunk_id": f"{doc_id}_p{page_number}_c{idx}",
                    "document_id": doc_id,
                    "page_number": page_number,
                    "chunk_index": idx,
                    "text": chunk_content,
                    "char_count": len(chunk_content),
                    "strategy": "fixed_character"
                })
                idx += 1
                
            if end >= text_len:
                break
            start += step
            
        return chunks

def save_document_chunks(doc_id, chunks, chunks_dir):
    """Saves the array of generated chunks to a JSON file."""
    os.makedirs(chunks_dir, exist_ok=True)
    chunks_path = os.path.join(chunks_dir, f"{doc_id}_chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
