import weaviate
import os
from dotenv import load_dotenv

load_dotenv()

def connect_to_weaviate():
    """Establish connection to Weaviate Cloud"""
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=os.getenv("WEAVIATE_URL"),
        auth_credentials=weaviate.auth.Auth.api_key(os.getenv("WEAVIATE_API_KEY"))
    )
    return client

def create_schema(client):
    """Create the Meeting Notes schema in Weaviate"""
    # First check if the class already exists
    try:
        client.collections.delete("MeetingNote")
        print("Existing MeetingNote class deleted.")
    except:
        pass
    
    # Define the class schema with proper property format
    meeting_notes = client.collections.create(
        name="MeetingNote",
        description="A collection of meeting notes for analysis",
        vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_weaviate(),
        generative_config=weaviate.classes.config.Configure.Generative.cohere(),
        properties=[
            weaviate.classes.config.Property(
                name="title", 
                data_type=weaviate.classes.config.DataType.TEXT,
                description="The title of the meeting"
            ),
            weaviate.classes.config.Property(
                name="date", 
                data_type=weaviate.classes.config.DataType.DATE,
                description="The date when the meeting was held"
            ),
            weaviate.classes.config.Property(
                name="participants", 
                data_type=weaviate.classes.config.DataType.TEXT_ARRAY,
                description="List of participants in the meeting"
            ),
            weaviate.classes.config.Property(
                name="content", 
                data_type=weaviate.classes.config.DataType.TEXT,
                description="The full content of the meeting notes"
            ),
            weaviate.classes.config.Property(
                name="summary", 
                data_type=weaviate.classes.config.DataType.TEXT,
                description="A summary of the meeting"
            )
        ]
    )
    
    print("MeetingNote class created successfully.")
    return meeting_notes

if __name__ == "__main__":
    client = connect_to_weaviate()
    if client:
        create_schema(client)
        print("Schema setup complete.")
        client.close()
    else:
        print("Failed to connect to Weaviate.")