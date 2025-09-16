import uuid
from pathlib import Path
import sys
from datetime import datetime, timezone

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import FAISS
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import CustomException 
from utils.model_loader import ModelLoader


class MultiDocIngestor:
    SUPPORTED_FILE_TYPES = {'.pdf', '.docx', '.txt', '.md'} # supported files for ingestion
    def __init__(self, temp_dir: str = "data/multi_doc_chat", faiss_dir: str = "faiss_index", session_id: str | None = None):
        try:
            # Base directories
            self.temp_dir = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.faiss_dir = Path(faiss_dir)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)

            # session management
            self.session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            self.session_temp_dir = self.temp_dir / self.session_id    
            self.session_faiss_dir = self.faiss_dir / self.session_id
            self.session_temp_dir.mkdir(parents=True, exist_ok=True)
            self.session_faiss_dir.mkdir(parents=True, exist_ok=True)

            self.model_loader = ModelLoader()
            log.info(
                "Document ingestor initialized", 
                temp_dir=str(self.temp_dir),
                faiss_dir=str(self.faiss_dir),
                session_id=self.session_id, 
                temp_path=str(self.session_temp_dir), 
                faiss_path=str(self.session_faiss_dir)
                )

        except Exception as e:
            log.error("Failed to initialize MultiDocIngestor", error=str(e))
            raise CustomException("Initialization error in MultiDocIngestor", sys)


    def ingest_files(self, uploaded_files):
        try:
            documents = []
            for uploaded_file in uploaded_files:
                ext = Path(uploaded_file.name).suffix.lower() 
                if ext not in self.SUPPORTED_FILE_TYPES:
                    log.warning("Unsupported file type skipped", file_name=uploaded_file.name)
                    continue

                unique_filename = f"{uuid.uuid4().hex[:8]}{ext}"  
                temp_path = self.session_temp_dir / unique_filename

                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.read())
                log.info("File saved for ingestion", filename=uploaded_file.name, saved_as=str(temp_path), session_id=self.session_id)

                if ext == '.pdf':
                    loader = PyPDFLoader(str(temp_path))
                elif ext == ".docx":
                    loader = Docx2txtLoader(str(temp_path))
                elif ext == ".txt":
                    loader = TextLoader(str(temp_path), encoding='utf8')
                else:
                    log.warning("Unsupported file type encountered", file_name=uploaded_file.name)
                    continue

                docs = loader.load()
                documents.extend(docs)

            if not documents:
                raise CustomException("No valid documents loaded for ingestion", sys)

            log.info("All documents loaded", total_documents=len(documents), session_id=self.session_id)

            return self._create_retriever(documents)
        
        except Exception as e:
            log.error("Failed to ingest files", error=str(e))
            raise CustomException("File ingestion error in MultiDocIngestor", sys)


    def _create_retriever(self, documents):
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=300)
            chunks = splitter.split_documents(documents)
            log.info("Document split into chunks completed", num_chunks=len(chunks), session_id=self.session_id)

            embeddings = self.model_loader.load_embeddings()

            vectorstore = FAISS.from_documents(documents=chunks, embedding=embeddings)

            # save FAISS index
            vectorstore.save_local(str(self.session_faiss_dir))  # saving the faiss index to session specific faiss directory
            log.info("FAISS index created and saved to disk", faiss_path=str(self.session_faiss_dir), session_id=self.session_id)

            retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
            log.info("FAISS Retriever created successfully", retriever_type=str(type(retriever)), session_id=self.session_id)
            return retriever
        
        except Exception as e:
            log.error("Failed to create retriever", error=str(e))
            raise CustomException("Retriever creation error in MultiDocIngestor", sys)
    