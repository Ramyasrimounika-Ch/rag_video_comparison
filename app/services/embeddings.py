from langchain_community.embeddings import HuggingFaceEmbeddings

embedding_model = None

def get_embedding_model():
    global embedding_model

    if embedding_model is None:
        embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5"
        )

    return embedding_model