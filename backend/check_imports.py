import sys
print(f"Python: {sys.executable}")
try:
    import langchain
    print(f"Langchain version: {langchain.__version__}")
    print(f"Langchain path: {langchain.__file__}")
    import langchain.chains
    print("langchain.chains imported")
    from langchain.chains import RetrievalQA
    print("RetrievalQA imported")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
