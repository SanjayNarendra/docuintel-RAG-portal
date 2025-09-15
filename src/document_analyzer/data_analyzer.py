import os
import sys
from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException
from model.models import *
from prompt.prompt_library import PROMPT_REGISTRY 
from logger import GLOBAL_LOGGER as log

from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser


class DocumentAnalyzer:
    """
    Analyzes documents using a pre-trained model.
    Automatically logs all actions and supports session-based organization.
    """
    def __init__(self):
        try:
            self.loader = ModelLoader()
            self.llm = self.loader.load_llm()

            # Prepare parsers
            self.parser = JsonOutputParser(pydantic_object=Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)

            self.prompt = PROMPT_REGISTRY["document_analysis"]
                
            log.info("DocumentAnalyzer initialized successfully")

        except Exception as e:
            log.error(f"Error initializing DocumentAnalyzer: {e}")
            raise CustomException(f"DocumentAnalyzer initialization failed: {e}")


    def analyze_document(self, document_text: str) -> dict:
        """
        Analyzes a document's text and extract structured metadata and summary.
        """
        try:
            chain = self.prompt | self.llm | self.fixing_parser
            log.info(f"Metadata analysis chain initialized.")

            response = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "document_text": document_text
            })
            
            log.info(f"Metadata extraction successful", keys=list(response.keys()))

            return response

        except Exception as e:
            log.error(f"Metadata analysis failed", error=str(e))
            raise CustomException(f"Metadata extraction failed", sys)

