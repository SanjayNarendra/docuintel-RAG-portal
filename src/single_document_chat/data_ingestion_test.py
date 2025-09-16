import uuid
from pathlib import Path
import sys
from datetime import datetime, timezone

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import FAISS
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import CustomException 
from utils.model_loader import ModelLoader

class SingleDocIngestor:
    def __init__(self, data_dir: str="data/single_document_chat", faiss_dir: str="faiss_index"):
        try:
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)

            self.faiss_dir = Path(faiss_dir)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)

            self.model_loader = ModelLoader()

            log.info("Single DocIngestor initialized", temp_path=str(self.data_dir), faiss_path=str(self.faiss_dir))

        except Exception as e:
            log.error("Failed to initialize SingleDocIngestor", error=str(e))
            raise CustomException("SingleDocIngestor initialization failed", sys)


    def ingest_files(self, uploaded_files):
        try:
            documents = []
            for uploaded_file in uploaded_files:
                unique_filename = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"
                temp_path = self.data_dir / unique_filename
                
                with open(temp_path, "wb") as f_out:
                    f_out.write(uploaded_file.read())
                log.info("PDF saved for ingestion", filename=uploaded_file.name)
                
                loader = PyPDFLoader(str(temp_path))
                docs = loader.load()
                documents.extend(docs)     

            log.info("PDF files loaded", num_documents=len(documents))

            return self._create_retriever(documents)
        
        except Exception as e:
            log.error("Document ingestion failed", error=str(e))
            raise CustomException("Error ingesting files", sys)
        

    def _create_retriever(self, documents):
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=300)
            chunks = splitter.split_documents(documents)
            log.info("Document split into chunks completed", num_chunks=len(chunks))

            embeddings = self.model_loader.load_embeddings()

            vectorstore = FAISS.from_documents(documents=chunks, embedding=embeddings)

            # save FAISS index
            vectorstore.save_local(str(self.faiss_dir), index_name="index")
            log.info("FAISS index created and saved", faiss_path=str(self.faiss_dir))

            retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
            log.info("Retriever created successfully", retriever_type=str(type(retriever)))
            return retriever

        except Exception as e:
            log.error("Failed to create retriever", error=str(e))
            raise CustomException("Error creating retriever", sys)