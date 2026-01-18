from sentence_transformers import SentenceTransformer
import os

print("Starting download of 'sentence-transformers/all-MiniLM-L6-v2'...")
print("This might take a while depending on your internet connection.")

try:
    # This will download the model to the default cache directory
    # usually ~/.cache/torch/sentence_transformers
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("Model downloaded successfully!")
except Exception as e:
    print(f"Error downloading model: {e}")
