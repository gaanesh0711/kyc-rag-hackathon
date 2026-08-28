import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()

PROMPT_TEMPLATE = """You are a fintech regulatory research assistant. Answer ONLY using the excerpts below. If they don't contain enough information, say so clearly. Do not state or imply that any company has violated a regulation — only describe applicable regulatory considerations and potential impacts, as the source data does.

Excerpts:
{context}

Question: {question}

Answer, and cite the company name and source document for each claim."""

PROMPT = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)


class RetrievalQAChain:
    """
    RetrievalQA chain implementation powered by Gemini API,
    retrieving source documents and returning answer + source_documents.
    """
    def __init__(self, retriever, llm, prompt: PromptTemplate, return_source_documents: bool = True):
        self.retriever = retriever
        self.llm = llm
        self.prompt = prompt
        self.return_source_documents = return_source_documents

    def format_docs(self, docs: List[Document]) -> str:
        return "\n\n---\n\n".join(doc.page_content for doc in docs)

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        query = inputs.get("query") or inputs.get("question")
        if not query:
            raise ValueError("Input must contain 'query' or 'question'")

        # Retrieve relevant chunks
        docs = self.retriever.invoke(query)

        # Format context and send to Gemini
        formatted_context = self.format_docs(docs)
        formatted_prompt = self.prompt.format(context=formatted_context, question=query)
        response = self.llm.invoke(formatted_prompt)
        
        # Handle string or list of text blocks from modern Gemini SDK
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, list):
                answer = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            else:
                answer = str(content)
        else:
            answer = str(response)

        output = {
            "query": query,
            "result": answer.strip()
        }
        if self.return_source_documents:
            output["source_documents"] = docs

        return output

    def __call__(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return self.invoke(inputs)


def get_rag_chain(
    persist_directory: str = "chroma_db",
    embedding_model_name: str = "all-MiniLM-L6-v2",
    model_name: str = "gemini-3.5-flash-lite",
    temperature: float = 0.0,
    search_k: int = 3,
    return_source_documents: bool = True
) -> RetrievalQAChain:
    """
    Builds the RetrievalQA chain using the Chroma vector store and ChatGoogleGenerativeAI (Gemini).
    """
    # Check for Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        raise ValueError(
            "GEMINI_API_KEY or GOOGLE_API_KEY not found. "
            "Please add GEMINI_API_KEY=your_key to your .env file."
        )

    os.environ["GOOGLE_API_KEY"] = gemini_key

    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": search_k}
    )

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=gemini_key
    )

    return RetrievalQAChain(
        retriever=retriever,
        llm=llm,
        prompt=PROMPT,
        return_source_documents=return_source_documents
    )


def query_rag(question: str, chain: RetrievalQAChain = None) -> Dict[str, Any]:
    if chain is None:
        chain = get_rag_chain()
    return chain.invoke({"query": question})


if __name__ == "__main__":
    test_question = "What SEBI-related regulatory challenges does Zerodha face?"
    print(f"Question: {test_question}\n")

    try:
        chain = get_rag_chain()
        response = chain.invoke({"query": test_question})

        print("=" * 60)
        print("ANSWER:")
        print("=" * 60)
        print(response.get("result"))
        print("\n" + "=" * 60)
        print("SOURCE DOCUMENTS:")
        print("=" * 60)
        for idx, doc in enumerate(response.get("source_documents", []), start=1):
            meta = doc.metadata
            print(f"\n[Source {idx}]")
            print(f"Company: {meta.get('company_name')}")
            print(f"Regulator: {meta.get('regulator')}")
            print(f"Vertical: {meta.get('vertical')}")
            print(f"Source Document: {meta.get('source_doc')}")
            print(f"Excerpt:\n{doc.page_content}\n")
    except Exception as e:
        print(f"\nExecution error: {e}")
