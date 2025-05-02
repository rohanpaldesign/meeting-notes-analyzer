import weaviate
import os
import datetime
import re
from dotenv import load_dotenv
from setup_schema import connect_to_weaviate

load_dotenv()

def parse_meeting_note(file_path):
    """Parse a meeting note file to extract structured information"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extract metadata with basic parsing
    title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', content)
    date_match = re.search(r'Date:\s*(.+?)(?:\n|$)', content)
    participants_match = re.search(r'Participants:\s*(.+?)(?:\n|$)', content)
    
    title = title_match.group(1).strip() if title_match else "Untitled Meeting"
    
    # Parse date (assuming format like "2023-05-15" or "April 15, 2023")
    date_str = date_match.group(1).strip() if date_match else None
    try:
        if date_str:
            # Try different date formats
            formats = ["%Y-%m-%d", "%B %d, %Y", "%d/%m/%Y", "%m/%d/%Y"]
            for fmt in formats:
                try:
                    date_obj = datetime.datetime.strptime(date_str, fmt)
                    # Format in RFC3339 format with time component
                    date_str = date_obj.strftime("%Y-%m-%dT12:00:00Z")
                    break
                except ValueError:
                    continue
        else:
            # Default to current date in RFC3339 format
            date_str = datetime.datetime.now().strftime("%Y-%m-%dT12:00:00Z")
    except:
        date_str = datetime.datetime.now().strftime("%Y-%m-%dT12:00:00Z")
    
    # Parse participants
    participants = []
    if participants_match:
        participants_str = participants_match.group(1).strip()
        participants = [p.strip() for p in participants_str.split(',')]
    
    # Extract main content (everything after metadata)
    content_parts = content.split("---")
    main_content = content_parts[1].strip() if len(content_parts) > 1 else content
    
    # Generate a simple summary
    summary = f"Meeting about {title} held on {date_str} with {len(participants)} participants."
    
    return {
        "title": title,
        "date": date_str,
        "participants": participants,
        "content": main_content,
        "summary": summary,
        "file_name": os.path.basename(file_path)
    }

def ingest_meeting_notes(client, directory_path):
    """Ingest all meeting notes from a directory into Weaviate"""
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        return
    
    meeting_notes_collection = client.collections.get("MeetingNote")
    
    files = [f for f in os.listdir(directory_path) if f.endswith('.txt') or f.endswith('.md')]
    print(f"Found {len(files)} files to process")
    
    for file in files:
        file_path = os.path.join(directory_path, file)
        try:
            meeting_data = parse_meeting_note(file_path)
            
            # Import the data into Weaviate using the current API
            meeting_notes_collection.data.insert(meeting_data)
            
            print(f"Imported: {file}")
        except Exception as e:
            print(f"Error importing {file}: {e}")

if __name__ == "__main__":
    print("Starting data ingestion process...")
    client = connect_to_weaviate()
    if client:
        print("Connected to Weaviate successfully.")
        print("Looking for files in the data directory...")
        
        directory_path = "data"
        if not os.path.exists(directory_path):
            print(f"Error: Directory '{directory_path}' not found!")
        else:
            files = [f for f in os.listdir(directory_path) if f.endswith('.txt') or f.endswith('.md')]
            print(f"Found {len(files)} files: {files}")
            
            ingest_meeting_notes(client, directory_path)
        
        print("Data ingestion process completed.")
        client.close()
    else:
        print("Failed to connect to Weaviate.")