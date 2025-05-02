from flask import Flask, render_template, request, jsonify, redirect, url_for
from query_engine import MeetingNotesQueryEngine
from setup_schema import connect_to_weaviate
from data_ingestion import ingest_meeting_notes
import os

app = Flask(__name__)
query_engine = MeetingNotesQueryEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    search_type = request.form.get('search_type', 'hybrid')
    
    if search_type == 'text':
        results = query_engine.search_by_text(query)
    elif search_type == 'vector':
        results = query_engine.search_by_vector(query)
    else:  # hybrid
        results = query_engine.hybrid_search(query)
    
    # Convert Weaviate objects to dictionaries for the template
    processed_results = []
    for result in results:
        processed_results.append({
            'title': result.properties.get('title', 'No title'),
            'date': result.properties.get('date', 'No date'),
            'participants': result.properties.get('participants', []),
            'content': result.properties.get('content', ''),
            'summary': result.properties.get('summary', '')
        })
    
    return render_template('results.html', results=processed_results, query=query)

@app.route('/action_items', methods=['POST'])
def action_items():
    query = request.form.get('query', '')
    result = query_engine.extract_action_items(query_text=query)
    return jsonify(result)

@app.route('/summary', methods=['POST'])
def summary():
    query = request.form.get('query', '')
    result = query_engine.summarize_meeting(query_text=query)
    return jsonify(result)

@app.route('/ask', methods=['POST'])
def ask():
    question = request.form.get('question', '')
    result = query_engine.ask_about_meetings(question)
    return jsonify(result)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('meeting_notes')
    if not file:
        return jsonify({"error": "No file provided"})
    
    if not os.path.exists('data'):
        os.makedirs('data')
    
    file_path = os.path.join('data', file.filename)
    file.save(file_path)
    
    client = connect_to_weaviate()
    if client:
        ingest_meeting_notes(client, 'data')
        client.close()
        return jsonify({"message": "File uploaded and processed successfully"})
    else:
        return jsonify({"error": "Failed to connect to Weaviate"})

if __name__ == '__main__':
    app.run(debug=True)