from flask import Blueprint, request, jsonify
from openai import OpenAI
import logging
import os

chat_bp = Blueprint('chat', __name__)

# Initialize OpenAI client
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

@chat_bp.route('/chat', methods=['POST'])
def chat_completion():
    """
    Endpoint for handling chat completions
    Expected JSON payload:
    {
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    }
    """
    try:
        if not client:
            return jsonify({"error": "OpenAI API key not configured"}), 500
            
        data = request.get_json()

        # Validate required fields
        if not data or 'messages' not in data:
            return jsonify({"error": "Missing required 'messages' field"}), 400
        tabctx = data.get('tabctx')
        print(f"Tab Context: {tabctx}")

        # Extract parameters with defaults
        if tabctx == 'canvas_proc':
            messages = [{"role": "system", "content": "You are a process modeling expert."},
                        {"role": "user", "content": "When asked to return YAML, only return YAML, without any explanation, without surrounding markdown code markup."},
                        {"role": "user", "content": """Define a process as per the following instructions. 
                        The process should be described in YAML format as two arrays: Nodes and Edges. 
                        Node elements represent steps in the process and are represented as nodes and edges represent the process flow linking nodes together. Every node and edge should have a unique id.
                        Each node should always have a name attribute.
                        Example node YAML:
                        - id: 1
                          name: Start
                          type: start
                          description: Start of the process
                
                        Example edge YAML:
                        - id: 1
                          source: 1
                          target: 2
                          type: flow
                          description: Flow from Start to Task 1
                        """}]
        elif tabctx == 'canvas_agent':
            messages = [{"role": "system", "content": "You are an agent organiser."},
                        {"role": "user", "content": "When asked to return YAML, only return YAML, without any explanation, without surrounding markdown code markup."},
                        {"role": "user", "content": """Define an organization chart of agents to solve the process as per the following instructions. 
                        Try to organize agents in a tree sturucture in three levels if possible, where level 0 is the initial entry point, level 1 agents are supervisors of particular domains and level 2 agents are specialists.
                        The organization chart should be described in YAML format as two arrays: Nodes and Edges. 
                        Nodes array elements represent agents in the organization and edges array elements represent the agent flow linking nodes together. Every node and edge should have a unique id.
                        Each node should always have a name attribute.
                        Example node YAML:
                        Nodes:
                            - id: 1
                            name: Front desk
                            type: start
                            description: First line agent that responds to all queries
                
                        Example edge YAML:
                        Edges:
                            - id: 1
                            source: 1
                            target: 2
                            type: flow
                            description: Flow from Start to Task 1
                        """}]

        messages.extend(data['messages'])

        model = data.get('model', 'gpt-3.5-turbo')
        temperature = data.get('temperature', 0.7)

        # Create completion
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        print(response.choices[0].message.content)
        return jsonify({
            "response": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        })

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500