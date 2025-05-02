from setup_schema import connect_to_weaviate

def check_data():
    client = connect_to_weaviate()
    if client:
        try:
            # Check if the MeetingNote collection exists
            collections = client.collections.list_all()
            print(f"Available collections: {[c.name for c in collections]}")
            
            # Get all objects from the MeetingNote collection
            meeting_notes = client.collections.get("MeetingNote")
            objects = meeting_notes.query.fetch_objects(limit=100)
            
            print(f"Found {len(objects)} objects in MeetingNote collection:")
            for obj in objects:
                print(f"- {obj.properties.get('title', 'No title')} ({obj.properties.get('date', 'No date')})")
                
        except Exception as e:
            print(f"Error querying data: {e}")
        finally:
            client.close()
    else:
        print("Failed to connect to Weaviate.")

if __name__ == "__main__":
    check_data()