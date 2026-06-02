from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://07c18582-1e4a-4968-afb4-cc214a981fc3.sa-east-1-0.aws.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YzA1MWMxNmEtZDhjYi00NzJhLWIwYTktMjY3OGM5N2U5MzY1In0.QKaHqAMlns2Q28Vx4JUuFPALa1rleq-Wxn9rmpbq3Ws"
)

client.delete_collection("video_comparison")

print("Collection deleted")