# ==========================================================
# llm_engine.py – Initialize and test LLM connection
# ==========================================================
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from . import config

print("🧠 Initializing LLM engine (debug test mode)...")

def test_llm_connection():
    """
    Tests if the OpenAI key and model are valid by sending a small test prompt.
    """
    try:
        model_name = "gpt-4o-mini"
        print(f"[DEBUG] Attempting to initialize ChatOpenAI model: {model_name}")
        llm = ChatOpenAI(model=model_name, temperature=0.3, openai_api_key=config.OPENAI_KEY)

        test_prompt = "Hello! Please respond with a one-line confirmation that the LLM is active."
        print(f"[DEBUG] Sending test prompt: {test_prompt}")

        response = llm.invoke([HumanMessage(content=test_prompt)])
        print("[DEBUG] LLM raw response object:", response)

        print(f"✅ LLM test succeeded! Response: {response.content}")
        return True

    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False
