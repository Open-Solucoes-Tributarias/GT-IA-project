try:
    print("Attempting to import langchain_openai...")
    import langchain_openai
    print("Success langchain_openai")
except ImportError as e:
    print(f"FAILED langchain_openai: {e}")

try:
    print("Attempting to import langchain_community...")
    import langchain_community
    print("Success langchain_community")
except ImportError as e:
    print(f"FAILED langchain_community: {e}")

try:
    print("Attempting to import langchain...")
    import langchain
    print("Success langchain")
except ImportError as e:
    print(f"FAILED langchain: {e}")
