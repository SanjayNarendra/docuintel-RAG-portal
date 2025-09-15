import sys
from pathlib import Path
import fitz
#from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException
from logger import GLOBAL_LOGGER as log


class DocumentIngestion:
    def __init__(self, base_dir:str="data\\document_compare"):
        #self.log = CustomLogger.get_logger(__name__) 
        self.base_dir = Path(base_dir)  
        self.base_dir.mkdir(parents=True, exist_ok=True) 


    def delete_existing_files(self):
        """ 
        Deletes existing files at the specified paths. 
        """
        try:
            if self.base_dir.exists() and self.base_dir.is_dir(): 
                for file in self.base_dir.iterdir(): 
                    if file.is_file():
                        file.unlink()  
                        log.info("File deleted", path=str(file))
                log.info("Directory cleaned", directory=str(self.base_dir))

        except Exception as e:
            log.error("Error deleting existing files: {e}")
            raise CustomException("An error occurred while deleting existing files", sys)
        

    def save_uploaded_files(self, reference_file, actual_file):
        """ 
        Saves uploaded files to a specific directory
        """
        try:
            self.delete_existing_files()  
            log.info("Existing files deleted successfully")

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
            raise CustomException("An error occurred while saving uploaded files", sys)
        

    def read_pdf(self, pdf_path: Path) -> str:
        """ 
        Read a PDF file and extracts text from each page. 
        """
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError(f"PDF is encrypted: {pdf_path.name}") 
                parts = []
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)  
                    text = page.get_text()   
                    
                    if text.strip(): 
                        parts.append(f"\n --- Page {page_num + 1} --- \n{text}") 

            log.info("PDF read successfully", file=str(pdf_path), pages=len(parts))
            return "\n".join(parts)
        
        except Exception as e:
            log.error("Error reading PDF: {e}")
            raise CustomException("An error occurred while reading the PDF", sys)

    
    def combine_documents(self):
        try:
            content_dict = {}
            doc_parts = []

            for filename in sorted(self.base_dir.iterdir()):
                if filename.is_file() and filename.suffix.lower() == ".pdf":
                    content_dict [filename.name] = self.read_pdf(filename)

            for filename, content in content_dict.items():
                doc_parts.append(f"Document: {filename}\n{content}")

            combined_text = "\n\n".join(doc_parts)
            log.info("Documents combined", count=len(doc_parts))
            return combined_text
        
        except Exception as e:
            log.error("Error combining documents: {e}")
            raise CustomException("An error occurred while combining documents", sys)




