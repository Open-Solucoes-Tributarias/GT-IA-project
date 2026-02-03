import pkgutil
import langchain
import langchain.chains

print(f"Langchain version: {langchain.__version__}")
print(f"Chains path: {langchain.chains.__path__}")

try:
    from langchain.chains import RetrievalQA
    print("Found RetrievalQA in langchain.chains")
except ImportError:
    print("RetrievalQA NOT in langchain.chains")
    
import langchain_community
print(f"Langchain Community version: {langchain_community.__version__}")
