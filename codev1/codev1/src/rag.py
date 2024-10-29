#write code to load all local files to memory for RAG
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
import os
import re
from langchain_chroma import Chroma
from codev1.src.utils import cprint


embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# vector_store = InMemoryVectorStore(embedding=embeddings)

vector_store = Chroma(
    collection_name="codebase",
    embedding_function=embeddings,
)

# from langchain_qdrant import QdrantVectorStore
# from qdrant_client import QdrantClient
# from qdrant_client.http.models import Distance, VectorParams

# client = QdrantClient(":memory:")

# client.create_collection(
#     collection_name="demo_collection",
#     vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
# )

# vector_store = QdrantVectorStore(
#     client=client,
#     collection_name="demo_collection",
#     embedding=embeddings,
# )

def read_gitignore_patterns(directory_path):
    """Reads .gitignore file and returns a list of patterns to ignore."""
    gitignore_path = os.path.join(directory_path, '.gitignore')
    patterns = []

    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as gitignore_file:
            patterns = [line.strip() for line in gitignore_file if line.strip() and not line.startswith('#')]

    return patterns

def is_ignored(file_path, ignore_patterns):
    """Checks if a file matches any of the ignore patterns."""
    for pattern in ignore_patterns:
        if re.search(pattern, file_path):
            return True
        # Check if the file path matches the pattern
    return False

def is_binary(file_path):
    """Checks if the file is binary."""
    try:
        with open(file_path, 'rb') as file:
            # Read a small portion of the file to check for binary content
            chunk = file.read(1024)
            if b'\0' in chunk:
                return True
    except Exception as e:
        cprint(f"Error checking if binary {file_path}: {e}", "error")
    return False
# Function to iterate over all local files and read their content
def read_all_files(directory_path):
    files_content = {}
    # Get ignore patterns from .gitignore file
    ignore_patterns = read_gitignore_patterns(directory_path)

    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Check if the file should be ignored
            if is_ignored(file_path, ignore_patterns) or is_binary(file_path):
                continue
              
              
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    files_content[file_path] = f.read()
            except Exception as e:
                cprint(f"Error reading {file_path}: {e}", "error")

    return files_content

def read_file(file_path):
    files_content = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            files_content[file_path] = f.read()
    except Exception as e:
        cprint(f"Error reading {file_path}: {e}", "error")

    return files_content

def load_embed_files(file_path):
    file_content = read_file(file_path)
    for file_path, content in file_content.items():
        vector_store.add_documents([Document(page_content=f"contents of filepath = {file_path} \n {content}", metadata={"source": file_path, "file_path": file_path })])
         
def embed_for_created_files(file_path):
    load_embed_files(file_path)

def update_embed_files(doc_id, file_path):
    
    file_content = read_file(file_path)
    for file_path, content in file_content.items():
        vector_store.update_document(doc_id, Document(page_content=f"contents of filepath = {file_path} \n {content}", metadata={"source": file_path, "file_path": file_path }))

    print(vector_store.get())
def find_doc_id(file_path):
    docs = vector_store.get()
    for idx, doc in enumerate(docs['metadatas']):
        if doc["source"] == file_path:
            return docs['ids'][idx]
        
def embed_for_updated_files(file_path):     
    doc_id = find_doc_id(file_path)
    update_embed_files(doc_id, file_path)

def embed_for_deleted_files(file_path):
    doc_id = find_doc_id(file_path)
    vector_store.delete(doc_id)

    print(vector_store.get())

# Example usage
def getDocs():
    # directory_path = os.getcwd()
    
    directory_path = '/Users/saravanan/base/code-assist/codev1/codev1/src'
    all_files_content = read_all_files(directory_path)
    documents = []
    for file_path, content in all_files_content.items():
        documents.append(Document(page_content=f"contents of filepath = {file_path} \n {content}", metadata={"source": file_path, "file_path": file_path }))
    
    return documents

def loadRAG():
    docs = getDocs()
    if len(docs) > 0:
        vector_store.add_documents(docs)

    print(vector_store.get())


def retrieve(query):
    results = vector_store.similarity_search_with_score(
        query=query, k=1
    )
    
    return results

def getContext(query):
    results = retrieve(query)
    context = ""
    for res, score in results:
        context += f"""{res.page_content} - \n score: {score}"""
    
    cprint("===============================context==============================","context")
    cprint(context, "context")
    return context


# loadRAG()
# getContext("getContext")