from flask import Blueprint, request, jsonify
from agents import get_orchestrator, AgentState
import logging

agent_bp = Blueprint('agents', __name__)

@agent_bp.route('/agents/chat', methods=['POST'])
def agent_chat():
    """
    Endpoint for multi-agent conversation processing
    Expected JSON payload:
    {
        "message": "Hello, I need help with an incident",
        "session_id": "user_session_123",
        "agent_id": "N0" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Missing required 'message' field"}), 400
        
        message = data['message']
        session_id = data.get('session_id', 'default')
        agent_id = data.get('agent_id')
        
        # Get orchestrator for user's organization and process conversation
        current_user = request.current_user if hasattr(request, 'current_user') else None
        organization_id = current_user['organization_id'] if current_user else None
        orchestrator = get_orchestrator(organization_id)
        
        if agent_id:
            # Direct agent interaction
            state = AgentState()
            result = orchestrator.execute_agent_action(agent_id, message, state)
        else:
            # Full conversation processing with routing
            result = orchestrator.process_conversation(message, session_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error processing agent chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/agents/organization', methods=['GET'])
def get_agent_organization():
    """Get the complete agent organization structure"""
    try:
        orchestrator = get_orchestrator()
        organization = orchestrator.get_agent_organization()
        return jsonify(organization)
    except Exception as e:
        logging.error(f"Error fetching agent organization: {str(e)}")
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/agents/config', methods=['GET'])
def get_agent_config():
    """Get specific agent configuration"""
    try:
        agent_id = request.args.get('agent_id')
        if not agent_id:
            return jsonify({"error": "Missing agent_id parameter"}), 400
        
        orchestrator = get_orchestrator()
        agent = orchestrator.get_agent_by_id(agent_id)
        
        if not agent:
            return jsonify({"error": f"Agent {agent_id} not found"}), 404
        
        return jsonify({
            "id": agent.id,
            "label": agent.label,
            "level": agent.level.value,
            "prompt": agent.prompt,
            "tools": agent.tools,
            "name": agent.name
        })
        
    except Exception as e:
        logging.error(f"Error fetching agent config: {str(e)}")
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/agents/route', methods=['POST'])
def agent_route():
    """
    Endpoint for agent routing decisions
    Expected JSON payload:
    {
        "current_agent": "N0",
        "message": "I need help with payroll",
        "context": {}
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'current_agent' not in data or 'message' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        current_agent = data['current_agent']
        message = data['message']
        context = data.get('context', {})
        
        orchestrator = get_orchestrator()
        next_agent = orchestrator.route_to_next_agent(current_agent, message, context)
        
        agent_config = orchestrator.get_agent_by_id(next_agent)
        
        return jsonify({
            "next_agent": next_agent,
            "agent_label": agent_config.label if agent_config else "Unknown",
            "agent_level": agent_config.level.value if agent_config else 0,
            "tools": agent_config.tools if agent_config else []
        })
        
    except Exception as e:
        logging.error(f"Error processing agent routing: {str(e)}")
        return jsonify({"error": str(e)}), 500