import os
import sys
import json
from dotenv import load_dotenv
from utils.config_loader import load_config

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

load_dotenv()


class ModelLoader:
    """
    A utility class to load embedding and LLM models 
    """
    def __init__(self):
        #load_dotenv()
        self._validate_env()
        self.config = load_config()
        logger.info("Configuration loaded successfully", config_keys=list(self.config.keys()))


    def _validate_env(self):
        """
        Validate necessary environment variables and ensure API keys exist.
        """
        required_vars = ['GOOGLE_API_KEY', 'GROQ_API_KEY']
        self.api_keys = {key:os.getenv(key) for key in required_vars}

        missing = [key for key, value in self.api_keys.items() if not value]
        if missing:
            logger.error("Missing environment variables", missing_vars=missing)
            raise CustomException("Missing environment variables", sys)
        
        logger.info("Environment variables validated successfully", available_keys=[key for key in self.api_keys if self.api_keys[key]])


    def load_embeddings(self):
        """
        Load and return the embedding mode.
        """
        try:
            embedding_model = self.config["embedding_model"]["model_name"]
            logger.info("Embedding model loaded successfully", model=embedding_model)
            return GoogleGenerativeAIEmbeddings(model=embedding_model)
               
        except Exception as e:
            logger.error("Error loading embedding model", error=str(e))
            raise CustomException(e, sys)


    def load_llm(self):
        """
        Load and return the LLM model.
        """
        llm_block = self.config["llm"]
        #model_name = llm_block["grok"]["model_name"]
        provider_key = os.getenv("LLM_PROVIDER", "groq")   # default groq

        if provider_key not in llm_block:
            logger.error("LLM provider not found in config", provider_key=provider_key)
            raise ValueError(f"Provider {provider_key} not found in config")
        
        llm_config = llm_block[provider_key]
        provider = llm_config.get("provider")
        model_name = llm_config.get("model_name")
        temperature = llm_config.get("temperature", 0.2)
        max_tokens = llm_config.get("max_output_tokens", 2048)

        logger.info("Loading LLM model", provider=provider, model=model_name, temperature=temperature, max_tokens=max_tokens)

        if provider == "google":
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=self.api_keys.get("GOOGLE_API_KEY"),
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            return llm

        elif provider == "groq":
            llm = ChatGroq(
                model=model_name,
                api_key=self.api_keys.get("GROQ_API_KEY"), #type: ignore
                temperature=temperature,
            )
            return llm
        
        else:
            logger.error("Unsupported LLM provider", provider=provider)
            raise ValueError(f"Unsupported provider: {provider}")

if __name__ == "__main__":
    loader = ModelLoader()

     # Test Embedding
    embeddings = loader.load_embeddings()
    print(f"Embedding Model Loaded: {embeddings}")
    result = embeddings.embed_query("Hello, how are you?")
    print(f"Embedding Result: {result}")

    # Test LLM
    llm = loader.load_llm()
    print(f"LLM Loaded: {llm}")
    result = llm.invoke("Hello, how are you?")
    print(f"LLM Result: {result.content}")