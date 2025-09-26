import os
import sys
import json
from dotenv import load_dotenv
from utils.config_loader import load_config

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq

from logger import GLOBAL_LOGGER as log
from exception.custom_exception import CustomException

#load_dotenv()

class ApiKeyManager:
    REQUIRED_KEYS = ["GROQ_API_KEY", "GOOGLE_API_KEY"]

    def __init__(self):
        self.api_keys = {}
        raw = os.getenv("API_KEYS")

        if raw:
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("API_KEYS is not a valid JSON object")
                self.api_keys = parsed
                log.info("Loaded API_KEYS from ECS secret")
            except Exception as e:
                log.warning("Failed to parse API_KEYS as JSON", error=str(e))

        # Fallback to individual env vars
        for key in self.REQUIRED_KEYS:
            if not self.api_keys.get(key):
                env_val = os.getenv(key)
                if env_val:
                    self.api_keys[key] = env_val
                    log.info(f"Loaded {key} from individual env var")

        missing = [k for k in self.REQUIRED_KEYS if not self.api_keys.get(k)]
        if missing:
            log.error("Missing required API keys", missing_keys=missing)
            raise CustomException("Missing API keys", sys)

        log.info("API keys loaded", keys={k: v[:6] + "..." for k, v in self.api_keys.items()})


    def get(self, key: str) -> str:
        val = self.api_keys.get(key)
        if not val:
            raise KeyError(f"API key for {key} is missing")
        return val


class ModelLoader:
    """
    A utility class to load embedding and LLM models 
    """
    def __init__(self):
        if os.getenv("ENV", "local").lower() != "production":
            load_dotenv()
            log.info("Running in LOCAL mode: .env loaded")
        else:
            log.info("Running in PRODUCTION mode")

        self.api_key_mgr = ApiKeyManager()
        self.config = load_config()
        log.info("YAML config loaded", config_keys=list(self.config.keys()))


    def load_embeddings(self):
        """
        Load and return the embedding mode.
        """
        try:
            embedding_model = self.config["embedding_model"]["model_name"]
            log.info("Embedding model loaded successfully", model=embedding_model)
            return GoogleGenerativeAIEmbeddings(model=embedding_model, google_api_key=self.api_key_mgr.get("GOOGLE_API_KEY")) #type: ignore
               
        except Exception as e:
            log.error("Error loading embedding model", error=str(e))
            raise CustomException("Failed to load embedding model", sys)


    def load_llm(self):
        """
        Load and return the LLM model.
        """
        llm_block = self.config["llm"]
        #model_name = llm_block["grok"]["model_name"]
        provider_key = os.getenv("LLM_PROVIDER", "groq")   # default groq

        if provider_key not in llm_block:
            log.error("LLM provider not found in config", provider_key=provider_key)
            raise ValueError(f"LLM provider {provider_key} not found in config")
        
        llm_config = llm_block[provider_key]
        provider = llm_config.get("provider")
        model_name = llm_config.get("model_name")
        temperature = llm_config.get("temperature", 0.2)
        max_tokens = llm_config.get("max_output_tokens", 2048)

        log.info("Loading LLM model", provider=provider, model=model_name, temperature=temperature, max_tokens=max_tokens)

        if provider == "google":
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=self.api_key_mgr.get("GOOGLE_API_KEY"),
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            return llm

        elif provider == "groq":
            llm = ChatGroq(
                model=model_name,
                api_key=self.api_key_mgr.get("GROQ_API_KEY"), #type: ignore
                temperature=temperature,
            )
            return llm
        
        else:
            log.error("Unsupported LLM provider", provider=provider)
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