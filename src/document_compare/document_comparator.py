import sys
from dotenv import load_dotenv
import pandas as pd

from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser

from model.models import *
from utils.model_loader import ModelLoader
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import CustomException
from prompt.prompt_library import PROMPT_REGISTRY


class DocumentComparatorLLM:
    def __init__(self):
        load_dotenv()
        self.loader = ModelLoader()
        self.llm = self.loader.load_llm()
        self.parser = JsonOutputParser(pydantic_object=SummaryResponse)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)
        self.prompt = PROMPT_REGISTRY[PromptType.DOCUMENT_COMPARISON.value]
        self.chain = self.prompt | self.llm | self.parser
        log.info("DocumentComparatorLLM initialized", model=self.llm)


    def compare_documents(self, combined_docs: str) -> pd.DataFrame:
        try:
            inputs = {
                "combined_docs": combined_docs,
                "format_instruction": self.parser.get_format_instructions()
            }
            log.info("Invoking document comparison LLM chain")
            response = self.chain.invoke(inputs)
            log.info("Chain invoked successfully", response_preview=str(response)[:200])
            return self._format_response(response)
        
        except Exception as e:
            log.error("Error in compare_documents", error=str(e))
            raise CustomException("Error comparing documents", sys)
        

    def _format_response(self, response_parsed: list[dict]) -> pd.DataFrame: #type: ignore
        """ Formats the LLM response into a pandas DataFrame (structured format)"""
        try:
            df = pd.DataFrame(response_parsed)
            log.info("Response formatted into DataFrame", dataframe=df) 
            return df
        
        except Exception as e:
            log.error("Error formatting response into DataFrame", error=str(e))
            CustomException("Error formatting response", sys)