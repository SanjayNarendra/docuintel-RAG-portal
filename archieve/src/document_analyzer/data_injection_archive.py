import sys
from pathlib import Path
import fitz
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException


class DocumentComparator:
    def __init__(self, base_dir):
        self.log = CustomLogger.get_logger(__name__)
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)  # create the base directory if it does not exist


    def delete_existing_files(self, file_paths):
        """ 
        Deletes existing files at the specified paths. 
        """
        try:
            if self.base_dir.exist() and self.base_dir.is_dir():
                for file in self.base_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                        self.log.info("File deleted", path=str(file))
                self.log.info("Directory cleaned", directory=str(self.base_dir))
                
        except Exception as e:
            self.log.error("Error deleting existing files: {e}")
            raise CustomException("An error occurred while deleting existing files", sys)
        

    def save_uploaded_files(self, reference_file, actual_file):
        """ 
        Saves uploaded files to a specific directory
        """
        try:
            self.delete_existing_files()
            self.log.info("Existing files deleted successfully")

            ref_path = self.session_path / reference_file.name
            act_path = self.session_path / actual_file.name

            if not reference_file.name.endswith(".pdf") or not actual_file.name.endswith(".pdf"):
                raise ValueError("Only PDF files are allowed.")
            
            with open(ref_path, "wb") as f:
                f.write(reference_file.getbuffer())

            with open(act_path, "wb") as f:
                f.write(actual_file.getbuffer())

            self.log.info("Files saved", reference=str(ref_path), actual=str(act_path))
            return ref_path, act_path
            
            # for fobj, out in ((reference_file, ref_path), (actual_file, act_path)):
            #     if not fobj.name.lower().endswith(".pdf"):
            #         raise ValueError("Only PDF files are allowed.")
            #     with open(out, "wb") as f:
            #         if hasattr(fobj, "read"):
            #             f.write(fobj.read())
            #         else:
            #             f.write(fobj.getbuffer())
            # self.log.info("Files saved", reference=str(ref_path), actual=str(act_path), session=self.session_id)
            # return ref_path, act_path
        
        except Exception as e:
            self.log.error("Error saving PDF files: {e}")
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
                    text = page.get_text()  # type: ignore
                    if text.strip():
                        parts.append(f"\n --- Page {page_num + 1} --- \n{text}")
            self.log.info("PDF read successfully", file=str(pdf_path), pages=len(parts))
            return "\n".join(parts)
        
        except Exception as e:
            self.log.error("Error reading PDF: {e}")
            raise CustomException("An error occurred while reading the PDF", sys)

