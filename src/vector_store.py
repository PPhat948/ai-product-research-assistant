import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import pandas as pd
from typing import List, Dict, Any

class VectorStoreManager:
    """
    Manages the ChromaDB vector store for semantic similarity search.
    Handles data ingestion and query processing using Google Generative AI Embeddings.
    """
    def __init__(self, persist_directory="./chroma_db"):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.persist_directory = persist_directory
        self.vector_store = Chroma(
            collection_name="products_collection",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def ingest_data(self, df: pd.DataFrame):
        """
        Ingests data into ChromaDB using Upsert logic.
        Handles monthly updates by updating existing products and adding new ones.
        """
        documents = []
        ids = []
        
        print(f"Ingesting {len(df)} products...")
        
        for _, row in df.iterrows():
            # Create a rich text representation for embedding
            content = f"""
            Product: {row['product_name']}
            Category: {row['category']}
            Brand: {row['brand']}
            Price: ${row['current_price']}
            Description: {row['description']}
            """
            
            # Metadata for filtering
            metadata = {
                "product_id": str(row['product_id']),
                "product_name": row['product_name'],
                "category": row['category'],
                "brand": row['brand'],
                "price": float(row['current_price']), # normalized key for search tool
                "stock_quantity": int(row['stock_quantity']),
                "average_rating": float(row['average_rating']),
                "review_count": int(row['review_count'])
            }
            
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
            # Use product_id as the unique ID for upsert
            ids.append(str(row['product_id']))
            
        if documents:
            # add_documents in Chroma handles upsert if IDs are provided
            # It will update if ID exists, insert if it doesn't.
            self.vector_store.add_documents(documents=documents, ids=ids)
            print("Ingestion complete.")
            
    def search(self, query: str, filter_dict: Dict[str, Any] = None, k: int = 4):
        """
        Performs similarity search with optional metadata filtering.
        """
        # We want to return scores as well
        results = self.vector_store.similarity_search_with_score(
            query,
            k=k,
            filter=filter_dict
        )
        return results

vector_store_manager = VectorStoreManager()
