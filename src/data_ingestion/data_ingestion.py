import os
import sys
import fitz  # PyMuPDF
import uuid
from datetime import datetime

#from logger.custom_logger import CustomLogger
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import CustomException


class DocumentHandler:
    """
    Handles PDF saving and reading operations.
    Automatically logs all actions and supports session-based organization.
    """

    def __init__(self, data_dir=None, session_id=None): 
        try:
            #self.logger = CustomLogger().get_logger(__name__)  
            self.data_dir = data_dir or os.getenv("DATA_STORAGE_PATH", os.path.join(os.getcwd(), "data", "document_analysis") )
            self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
           
            # create base session directory 
            self.session_path = os.path.join(self.data_dir, self.session_id)
            os.makedirs(self.session_path, exist_ok=True)
            #self.logger.info("DocumentHandler initialized", session_id=self.session_id, session_path=self.session_path)
            log.info("DocumentHandler initialized", session_id=self.session_id, session_path=self.session_path)

        except Exception as e:
            self.logger.error(f"Error initializing DocumentHandler: {e}")
            raise CustomException("Error initializing DocumentHandler", e, sys) 
            

    def save_pdf(self, uploaded_file):
        try:
            filename = os.path.basename(uploaded_file.name)
            
            if not filename.lower().endswith(".pdf"):
                raise ValueError("Invalid file type. Only PDFs are allowed.")
            
            save_path = os.path.join(self.session_path, filename)
            
            with open(save_path, "wb") as f:
                if hasattr(uploaded_file, "read"):
                    f.write(uploaded_file.read())
                else:
                    f.write(uploaded_file.getbuffer())
            
            log.info("PDF saved successfully", file=filename, save_path=save_path, session_id=self.session_id)
            return save_path

        except Exception as e:
            self.logger.error(f"Error saving PDF: {e}")
            raise CustomException("Error saving PDF", e) from e

    def read_pdf(self, pdf_path: str) -> str:
        try:
            text_chunks = [] 
            with fitz.open(pdf_path) as doc:  
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text_chunks.append(f"\n--- Page {page_num + 1} ---\n{page.get_text()}") 
            text = "\n".join(text_chunks)

            log.info("PDF read successfully", pdf_path=pdf_path, session_id=self.session_id, pages=len(text_chunks))

            return text
        
        except Exception as e:
            self.logger.error(f"Error reading PDF: {e}")
            raise CustomException("Error reading PDF", e) from e


# testing the class methods
if __name__ == "__main__":
    from pathlib import Path 
    from io import BytesIO
    
    #pdf_path = r"D:\\LLMOps\\00_resources\\docuintel-rag-portal\\document_portal\\data\\document_analysis\\NIPS-2017-attention-is-all-you-need-Paper.pdf"
    pdf_path = r"D:\LLMOps\docuintel-RAG-portal\notebook\data\sample.pdf"
    
    # this class is only for testing purpose to simulate the uploaded file object
    class DummyFile:
        def __init__(self, file_path):
            self.name = Path(file_path).name   
            self._file_path = file_path 
        
        def getbuffer(self):  
            return open(self._file_path, "rb").read()  
        
    dummy_pdf = DummyFile(pdf_path)  

    handler = DocumentHandler(session_id="test_session_001") 

    try:
       saved_path = handler.save_pdf(dummy_pdf)
       print(saved_path)

       content = handler.read_pdf(saved_path) 
       print(content[:500])

    except Exception as e:
        print(f"Error: {e}")