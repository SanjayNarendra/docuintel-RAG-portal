import sys
from pathlib import Path
import fitz
#from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException
from logger import GLOBAL_LOGGER as log

import uuid
from datetime import datetime, timezone


class DocumentIngestion:
    """ 
    Handles document ingestion, saving, reading, and combining PDFs for comparison with session-based versioning. 
    """
    def __init__(self, base_dir:str="data\\document_compare", session_id=None):
        #self.log = CustomLogger.get_logger(__name__) 
        self.base_dir = Path(base_dir)  
        self.base_dir.mkdir(parents=True, exist_ok=True) 

        self.session_id = session_id or f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        log.info("DocumentComparator initialized", session_path=str(self.session_path))


    # def delete_existing_files(self):
    #     """ 
    #     Deletes existing files at the specified paths. 
    #     """
    #     try:
    #         if self.base_dir.exists() and self.base_dir.is_dir(): 
    #             for file in self.base_dir.iterdir(): 
    #                 if file.is_file():
    #                     file.unlink()  
    #                     log.info("File deleted", path=str(file))
    #             log.info("Directory cleaned", directory=str(self.base_dir))

    #     except Exception as e:
    #         log.error("Error deleting existing files: {e}")
    #         raise CustomException("An error occurred while deleting existing files", sys)
        

    def save_uploaded_files(self, reference_file, actual_file):
        """ 
        Saves uploaded files in the session directory.
        """
        try:
            # self.delete_existing_files()  
            # log.info("Existing files deleted successfully")

            ref_path = self.base_dir / reference_file.name
            act_path = self.base_dir / actual_file.name

            if not reference_file.name.endswith(".pdf") or not actual_file.name.endswith(".pdf"):  
                raise ValueError("Only PDF files are allowed.") 
            
            with open(ref_path, "wb") as f: 
                f.write(reference_file.getbuffer())

            with open(act_path, "wb") as f: 
                f.write(actual_file.getbuffer())

            log.info("Files saved", reference=str(ref_path), actual=str(act_path))
            return ref_path, act_path

        
        except Exception as e:
            log.error("Error saving PDF files: {e}")
            raise CustomException("Error saving files ", sys)
        

    def read_pdf(self, pdf_path: Path) -> str:
        """ 
        Read a PDF file and extracts text from each page. 
        """
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError(f"PDF is encrypted: {pdf_path.name}") 
                all_text = []
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)  
                    text = page.get_text()   
                    
                    if text.strip(): 
                        all_text.append(f"\n --- Page {page_num + 1} --- \n{text}") 

            log.info("PDF read successfully", file=str(pdf_path), pages=len(all_text))
            return "\n".join(all_text)
        
        except Exception as e:
            log.error("Error reading PDF", file=str(pdf_path), error=str(e))
            raise CustomException("Error reading PDF", sys)

    
    def combine_documents(self) -> str:
        """
        Combine content of all PDFs in session folder into a single text string.
        """
        try:
            doc_parts = []
            for file in sorted(self.base_dir.iterdir()):
                if file.is_file() and file.suffix.lower() == ".pdf":
                    content = self.read_pdf(file)
                    doc_parts.append(f"Document: {file.name}\n{content}")

            combined_text = "\n\n".join(doc_parts)
            log.info("Documents combined", count=len(doc_parts), session=self.session_id)
            return combined_text
        
        except Exception as e:
            log.error("Error combining documents", error=str(e), session=self.session_id)
            raise CustomException("Error combining documents", sys)


    def clean_old_sessions(self, keep_latest:int = 3):
        """ 
        Optional method to delete older session folders, keeping only the latest N sessions.
        """
        try:
            session_folders = sorted(
                [f for f in self.base_dir.iterdir() if f.is_dir()], reverse=True
                )
            for folder in session_folders[keep_latest:]:
                for file in folder.iterdir():
                    file.unlink()
                folder.rmdir()
                log.info("Old session folder deleted", path=str(folder))

        except Exception as e:
            log.error("Error cleaning old sessions", error=str(e))
            raise CustomException("Error cleaning old sessions", sys)




