import re
import os
import pypdf
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Canonical vertical and regulator mapping
VERTICAL_MAP = {
    'Wealthtech_Investment_Platforms_Regulation_Problems_Dataset.pdf': {
        'vertical': 'Wealthtech & Investment Platforms',
        'regulator': 'SEBI'
    },
    'Insurtech_Regulation_Problems_Dataset.pdf': {
        'vertical': 'Insurtech',
        'regulator': 'IRDAI'
    },
    'Payment_Companies_PSPs_Regulation_Problems_Dataset.pdf': {
        'vertical': 'Payment Companies & PSPs',
        'regulator': 'RBI'
    },
    'Fintech_SaaS_B2B_Infrastructure_Regulation_Problems_Dataset.pdf': {
        'vertical': 'Fintech SaaS & B2B Infrastructure',
        'regulator': 'RBI / regulated financial-institution customers'
    },
    'Crypto_VDA_Platforms_Regulation_Problems_Dataset.pdf': {
        'vertical': 'Crypto & VDA Platforms',
        'regulator': 'FIU-IND / Income Tax Department / Government of India'
    },
    'Credit_Lending_Infrastructure_Regulation_Problems_Dataset.pdf': {
        'vertical': 'Credit & Lending Infrastructure',
        'regulator': 'RBI'
    },
    'PPI_Wallet_Companies_Regulation_Problems_Dataset(1).pdf': {
        'vertical': 'PPI & Wallets',
        'regulator': 'RBI'
    },
    'Payment_Aggregators_Regulation_Problems_Dataset_Final.pdf': {
        'vertical': 'Payment Aggregators',
        'regulator': 'RBI'
    }
}

KNOWN_REGULATORS = [
    'FIU-IND / Income Tax Department / Government of India',
    'RBI / regulated financial-institution customers',
    'IRDAI',
    'SEBI',
    'RBI'
]


def load_finvisory_dataset(pdf_path: str) -> List[Document]:
    """
    Parses FinVisory PDF ensuring that each company entry is kept intact
    as a single Document chunk with rich metadata (company_name, regulator, vertical, doc).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    reader = pypdf.PdfReader(pdf_path)
    
    # Extract text from pages 2 to 15 (page 1 is title, 16 is back-cover)
    full_text = ""
    for p in range(1, len(reader.pages) - 1):
        full_text += "\n" + reader.pages[p].extract_text()

    # Clean headers
    cleaned = re.sub(
        r'FinVisory\s+Page \d+\s+Name\s+Problem faced\s+Entity\s+Doc', '', full_text
    )

    # Match all .pdf filenames marking the end of each record
    matches = list(re.finditer(r'([A-Za-z0-9_\(\)]+\s*_\s*[A-Za-z0-9_\(\)\s]*\.pdf)', cleaned))
    
    documents = []
    last_pos = 0

    for idx, m in enumerate(matches):
        raw_block = cleaned[last_pos:m.end()].strip()
        last_pos = m.end()

        doc_str = re.sub(r'\s+', '', m.group(1))

        # Identify canonical document & vertical
        matched_v = None
        for k, v in VERTICAL_MAP.items():
            k_clean = re.sub(r'[^a-zA-Z0-9]', '', k).lower()
            d_clean = re.sub(r'[^a-zA-Z0-9]', '', doc_str).lower()
            if k_clean[:12] in d_clean or d_clean[:12] in k_clean:
                matched_v = (k, v)
                break

        canonical_doc = matched_v[0] if matched_v else doc_str
        vertical = matched_v[1]['vertical'] if matched_v else 'Fintech'
        default_reg = matched_v[1]['regulator'] if matched_v else 'RBI'

        # Text without the .pdf filename
        body = raw_block[:raw_block.rfind(m.group(1))].strip()
        norm_body = ' '.join(body.split())

        # Extract regulator entity
        entity = default_reg
        for reg in KNOWN_REGULATORS:
            if norm_body.endswith(reg):
                entity = reg
                norm_body = norm_body[:-len(reg)].strip()
                break

        # Separate Company Name from Problem Faced
        role_idx = norm_body.find('Role:')
        if role_idx != -1:
            comp_name = norm_body[:role_idx].strip()
            # Clean unwanted header artifacts and page numbers
            comp_name = re.sub(r'FinVisory[^\w]*Page\s*\d+', '', comp_name, flags=re.IGNORECASE).strip()
            comp_name = re.sub(r'\b(Name|Problem\s*faced|Entity|Doc)\b', '', comp_name, flags=re.IGNORECASE).strip()
            problem_faced = norm_body[role_idx:].strip()
        else:
            parts = norm_body.split(' ', 2)
            comp_name = parts[0]
            problem_faced = norm_body

        comp_name = ' '.join(comp_name.split()).strip()
        problem_faced = ' '.join(problem_faced.split()).strip()

        content = (
            f"Company: {comp_name}\n"
            f"Vertical / Sector: {vertical}\n"
            f"Regulator / Entity: {entity}\n"
            f"Source Document: {canonical_doc}\n\n"
            f"Regulatory Problem & Compliance Impact:\n{problem_faced}"
        )

        metadata = {
            "company_name": comp_name,
            "regulator": entity,
            "vertical": vertical,
            "source_doc": canonical_doc,
            "entry_index": idx + 1,
            "source": pdf_path
        }

        doc = Document(page_content=content, metadata=metadata)
        documents.append(doc)

    return documents


def rebuild_vector_store(
    pdf_path: str = "docs/FinVisory_Merged_Regulatory_Problems.pdf",
    persist_directory: str = "chroma_db",
    embedding_model_name: str = "all-MiniLM-L6-v2"
):
    import shutil
    if os.path.exists(persist_directory):
        print(f"Removing existing vector store directory '{persist_directory}' for clean rebuild...")
        shutil.rmtree(persist_directory)

    print(f"Loading and chunking dataset from: {pdf_path}...")
    docs = load_finvisory_dataset(pdf_path)
    print(f"Total structured company chunks created: {len(docs)}")

    print(f"Initializing embedding model: {embedding_model_name}...")
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

    print(f"Indexing {len(docs)} documents into ChromaDB at '{persist_directory}'...")
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    print("Vector store build complete and persisted successfully!")

    # Verification
    print("\n--- Vector Store Verification ---")
    collection = vector_store._collection
    count = collection.count()
    print(f"Total indexed items in ChromaDB: {count}")

    # Query verification test
    test_query = "What regulatory problems does Zerodha face?"
    print(f"\nRunning test similarity search for query: '{test_query}'...")
    results = vector_store.similarity_search_with_score(test_query, k=2)
    for i, (doc, score) in enumerate(results):
        print(f"\nResult {i+1} (Score: {score:.4f}):")
        print(f"Company: {doc.metadata.get('company_name')}")
        print(f"Regulator: {doc.metadata.get('regulator')}")
        print(f"Vertical: {doc.metadata.get('vertical')}")
        print(f"Excerpt: {doc.page_content[:200]}...")

    return vector_store


if __name__ == "__main__":
    rebuild_vector_store()

