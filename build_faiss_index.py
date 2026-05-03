# build_faiss_index.py
# Step 1 of RAG: Load documents → Chunk text → Create embeddings → Save FAISS index
#
# Run this script ONCE before starting the agent.
# You only need to re-run it if you update the RAG documents.
#
# pip install langchain langchain-community langchain-text-splitters
#             langchain-openai faiss-cpu pypdf docx2txt python-dotenv

import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

load_dotenv()

# ── config ────────────────────────────────────────────────────────────────────
RAG_FOLDER      = "rag_files"       # folder containing your RAG documents
FAISS_INDEX_PATH = "faiss_index"    # where the FAISS index will be saved

# ── step 1: load documents ────────────────────────────────────────────────────
# supports .txt and .docx files in the rag_files/ folder
# (Scout uses PyPDFLoader for PDFs — we use docx2txt for Word documents)
print("Loading documents...")
documents = []

for filename in os.listdir(RAG_FOLDER):
    filepath = os.path.join(RAG_FOLDER, filename)

    # ── .txt files ────────────────────────────────────────────────────────────
    if filename.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        documents.append(Document(
            page_content=text,
            metadata={"source": filename}
        ))
        print(f"  Loaded .txt: {filename}")

    # ── .docx files ───────────────────────────────────────────────────────────
    elif filename.endswith(".docx"):
        try:
            import docx2txt
            text = docx2txt.process(filepath)
            documents.append(Document(
                page_content=text,
                metadata={"source": filename}
            ))
            print(f"  Loaded .docx: {filename}")
        except ImportError:
            print(f"  Skipped {filename} — install docx2txt: pip install docx2txt")

    # ── .pdf files ────────────────────────────────────────────────────────────
    elif filename.endswith(".pdf"):
        try:
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            documents.extend(docs)
            print(f"  Loaded .pdf: {filename} ({len(docs)} pages)")
        except Exception as e:
            print(f"  Skipped {filename}: {e}")

print(f"\nTotal documents loaded: {len(documents)}")

if not documents:
    print("\nNo documents found in rag_files/ folder.")
    print("Add your RAG document(s) to the rag_files/ folder and re-run.")
    exit()

# ── step 2: split into chunks ─────────────────────────────────────────────────
# using a larger chunk size than Scout (500) because legal regulation sections
# are longer and need to stay mostly intact to preserve context.
# chunk_overlap ensures no regulation detail is lost at chunk boundaries.
print("\nSplitting into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,    # characters per chunk — keeps most regulation sections intact
    chunk_overlap=150,  # overlap between chunks to preserve context across boundaries
    separators=["\n\n", "\n", " ", ""]  # splits at paragraph breaks first
)
chunks = text_splitter.split_documents(documents)
print(f"Total chunks created: {len(chunks)}")

# print all chunks so you can inspect what was created
# (same as Scout's build_faiss_index.py — helpful for verifying quality)
print("\n--- CHUNK PREVIEW ---")
for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i + 1} ---")
    print(f"Source: {chunk.metadata.get('source', 'unknown')}")
    print(chunk.page_content[:300] + "..." if len(chunk.page_content) > 300 else chunk.page_content)

# ── step 3: create embeddings and build FAISS index ───────────────────────────
# this sends the chunks to OpenAI's embedding model to create vectors
# note: this costs tokens — only run when you need to update the index
print("\nCreating embeddings and building FAISS index...")
print("(This calls the OpenAI API and costs a small amount of tokens)")
embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY"))
vectorstore = FAISS.from_documents(chunks, embeddings)

# ── step 4: save the FAISS index to disk ──────────────────────────────────────
# saves two files: faiss_index/index.faiss and faiss_index/index.pkl
# the logic file loads these at startup with FAISS.load_local()
vectorstore.save_local(FAISS_INDEX_PATH)
print(f"\nDone! FAISS index saved to '{FAISS_INDEX_PATH}/'")
print("You can now run the agent with: streamlit run termstrust_app.py")
