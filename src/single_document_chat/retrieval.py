import sys
import os
from operator import itemgetter
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import streamlit as st

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from utils.model_loader import ModelLoader
from exception.custom_exception import CustomException
from logger import GLOBAL_LOGGER as log
from prompt.prompt_library import PROMPT_REGISTRY
from model.models import PromptType


class ConversationalRAG:
    """
    LCEL-based Conversational RAG with lazy retriever initialization.

    Usage:
        rag = ConversationalRAG(session_id="abc")
        rag.load_retriever_from_faiss(index_path="faiss_index/abc", k=5, index_name="index")
        answer = rag.invoke("What is ...?", chat_history=[])
    """

    def __init__(self, session_id: str, retriever):
        try:
            self.session_id = session_id
            self.retriever = retriever
            self.llm = self._load_llm()
            self.contextualize_prompt = PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt = PROMPT_REGISTRY[PromptType.CONTEXT_QA.value] 
            self.history_aware_retriever = create_history_aware_retriever(
                self.retriever, self.llm, self.contextualize_prompt
                )
            log.info("Created history aware retriever", session_id=session_id)
            
            self.qa_chain = create_stuff_documents_chain(self.llm, self.qa_prompt)
            self.rag_chain = create_retrieval_chain(self.history_aware_retriever, self.qa_chain)
            log.info("Created RAG chain", session_id=self.session_id)

            self.chain = RunnableWithMessageHistory(
                self.rag_chain, 
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer"
                )

        except Exception as e:
            log.error("Error initializing ConversationalRAG", error=str(e))
            raise CustomException("ConversationalRAG initialization failed", sys)
        

    def _load_llm(self):  
        try:
            llm = ModelLoader().load_llm()
            log.info("LLM loaded successfully", class_name=llm.__class__.__name__)
            return llm
            
        except Exception as e:
            log.error("Error loading LLM via ", error=str(e))
            raise CustomException("Error loading LLM", sys)


    def _get_session_history(self):
        try:
            return ChatMessageHistory.get_history(self.session_id)
        except Exception as e:
            log.error("Failed to get session history", error=str(e))
            raise CustomException("Error getting session history", sys)


    def load_retriever_from_faiss(self, index_path: str):
        try:
            embeddings = ModelLoader().load_embeddings()
            if not os.path.isdir(index_path):
                raise CustomException(f"FAISS index directory not found: {index_path}")

            vectorstore = FAISS.load_local(index_path, embeddings)
            log.info("Loaded retriever from FAISS index", index_path=index_path)
            return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

        except Exception as e:
            log.error("Error loading FAISS retriever", error=str(e))
            raise CustomException("Error loading FAISS retriever", sys)


    def invoke(self, user_input:str) -> str:
        try:
            response = self.chain.invoke(
                    {"input": user_input}, 
                    config={"configurable": {"session_id": self.session_id}}
                    )
            answer = response.get("answer", "No answer generated")
            if not answer:
                log.warning("No answer found", session_id=self.session_id)

            log.info("Chain invoked successfully", session_id=self.session_id, user_input=user_input, answer_preview=answer[:150])
            return answer

        except Exception as e:
            log.error("Error invoking ConversationalRAG", error=str(e))
            raise CustomException("Error during RAG invocation", sys)