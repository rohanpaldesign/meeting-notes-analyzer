import weaviate
import os
from dotenv import load_dotenv
from setup_schema import connect_to_weaviate

load_dotenv()

class MeetingNotesQueryEngine:
    def __init__(self):
        self.client = None
        self.collection = None
    
    def _ensure_connection(self):
        """Ensure we have an active connection to Weaviate"""
        if self.client is None:
            self.client = connect_to_weaviate()
            self.collection = self.client.collections.get("MeetingNote")
    
    def search_by_text(self, query_text, limit=5):
        """Search for meeting notes using text search"""
        self._ensure_connection()
        result = (
            self.collection.query.bm25(
                query=query_text,
                limit=limit
            )
        )
        
        return result.objects
    
    def search_by_vector(self, query_text, limit=5):
        """Search for meeting notes using vector search (semantic search)"""
        self._ensure_connection()
        result = (
            self.collection.query.near_text(
                query=query_text,
                limit=limit
            )
        )
        
        return result.objects
    
    def hybrid_search(self, query_text, limit=5):
        """Perform a hybrid search combining vector and BM25"""
        self._ensure_connection()
        result = (
            self.collection.query.hybrid(
                query=query_text,
                alpha=0.5,  # Balance between BM25 and vector search
                limit=limit
            )
        )
        
        return result.objects
    
    def extract_action_items(self, meeting_id=None, query_text=None):
        """Extract action items from meeting notes using Weaviate's generative feature"""
        self._ensure_connection()
        
        if meeting_id:
            # Get specific meeting by ID
            result = (
                self.collection.query.fetch_objects_by_id(
                    uuid=meeting_id,
                )
            )
            
            if not result or len(result) == 0:
                return {"error": "Meeting not found"}
            
            meeting_content = result[0].properties.get("content", "")
        elif query_text:
            # Use the query to find relevant meetings first
            relevant_meetings = self.hybrid_search(query_text, limit=1)
            if not relevant_meetings:
                return {"error": "No relevant meetings found"}
            
            # Use the first relevant meeting
            meeting_content = relevant_meetings[0].properties.get("content", "")
        else:
            return {"error": "Either meeting_id or query_text must be provided"}
        
        # Use Generate API to extract action items
        prompt = f"""
        Extract and list all action items from the following meeting notes. 
        For each action item, include:
        1. The task description
        2. The person assigned to it (if specified)
        3. The deadline (if specified)
        
        Format the output as a bulleted list.
        
        Meeting notes:
        {meeting_content}
        """
        
        result = self.collection.generate.single_prompt(
            prompt=prompt
        )
        
        return {"generated": result}
    
    def summarize_meeting(self, meeting_id=None, query_text=None):
        """Generate a summary of the meeting"""
        self._ensure_connection()
        
        if meeting_id:
            # Get specific meeting by ID
            result = (
                self.collection.query.fetch_objects_by_id(
                    uuid=meeting_id,
                )
            )
            
            if not result or len(result) == 0:
                return {"error": "Meeting not found"}
            
            meeting_content = result[0].properties.get("content", "")
        elif query_text:
            # Use the query to find relevant meetings first
            relevant_meetings = self.hybrid_search(query_text, limit=1)
            if not relevant_meetings:
                return {"error": "No relevant meetings found"}
            
            # Use the first relevant meeting
            meeting_content = relevant_meetings[0].properties.get("content", "")
        else:
            return {"error": "Either meeting_id or query_text must be provided"}
        
        # Use Generate API to summarize
        prompt = f"""
        Provide a concise summary of the following meeting notes.
        Include key points discussed, decisions made, and next steps.
        
        Meeting notes:
        {meeting_content}
        """
        
        result = self.collection.generate.single_prompt(
            prompt=prompt
        )
        
        return {"generated": result}

    def ask_about_meetings(self, question):
        """Ask a question about the meetings"""
        self._ensure_connection()
        
        # First do a hybrid search to find relevant meetings
        relevant_meetings = self.hybrid_search(question, limit=3)
        
        if not relevant_meetings:
            return {"error": "No relevant meetings found"}
        
        # Extract the content from each meeting
        contents = []
        for meeting in relevant_meetings:
            contents.append(meeting.properties.get("content", ""))
        
        # Create a prompt using the relevant meeting contents
        prompt = f"""
        Answer the following question based ONLY on the provided meeting notes content:
        
        Question: {question}
        
        Meeting notes:
        {"---".join(contents)}
        
        If the information is not in the meeting notes, state that clearly.
        """
        
        result = self.collection.generate.single_prompt(
            prompt=prompt
        )
        
        return {"generated": result}

    def close(self):
        """Close the connection to Weaviate"""
        if self.client:
            self.client.close()
            self.client = None
            self.collection = None

if __name__ == "__main__":
    # Test the query engine
    engine = MeetingNotesQueryEngine()
    results = engine.hybrid_search("project status updates")
    print(f"Found {len(results)} results")
    for r in results:
        print(f"Title: {r.properties.get('title')}")
        print(f"Date: {r.properties.get('date')}")
        print("---")
    engine.close()