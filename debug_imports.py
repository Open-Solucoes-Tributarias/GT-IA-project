import sys
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

try:
    print("1. Importing langchain_openai...")
    from langchain_openai import ChatOpenAI
    print("   Success.")
except ImportError as e:
    print(f"   FAILED: {e}")

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate
    from langchain.chains import RetrievalQA
except ImportError as e:
    print(f"DEBUG IMPORT: {e}")
    try:
        from langchain.chat_models import ChatOpenAI
        from langchain.prompts import PromptTemplate
        from langchain.chains import RetrievalQA
    except ImportError:
        pass

try:
    print("4. Importing openai...")
    import openai
    print("   Success.")
except ImportError as e:
    print(f"   FAILED: {e}")
