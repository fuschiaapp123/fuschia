const baseUrl = 'http://localhost:8000';
const url = `${baseUrl}/api/v1/chat`;

  
function parseJSON(response: Response) {
    // console.log('In Parse JSON' + response.text());
    return response.json();
    // return response.text();
}

const ChatAPI = async (ctx: string, msg: string, agentMode = false, agentId?: string) => {
    console.log('In Chat API: ' + ctx);
    
    if (agentMode) {
        // Use new agent chat endpoint
        const agentUrl = `${baseUrl}/api/v1/agents/chat`;
        const agentPayload = {
            message: msg,
            session_id: 'admin_session',
            agent_id: agentId
        };
        
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        
        try {
            const response = await fetch(agentUrl, {
                method: "POST",
                body: JSON.stringify(agentPayload),
                headers: myHeaders,
            });

            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            return parseJSON(response);
        } catch (e) {
            console.error(e);
            // Return mock response as fallback
            return {
                response: `Error connecting to agent chat service. Mock response for: "${msg}"`,
                agent_id: agentId,
                agent_label: 'Chat Agent (Fallback)'
            };
        }
    } else {
        // Original chat endpoint for workflow/canvas generation
        let tmpmsg = '{"messages": [{"role": "user", "content": "' + msg + '"}],"model": "gpt-3.5-turbo","temperature": 0.7, "tabctx":"' + ctx + '"}';
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        try {
            const response = await fetch(url, {
                method: "POST",
                body: tmpmsg,
                headers: myHeaders,
            });

            if (!response.ok) {
              throw new Error(`Response status: ${response.status}`);
            }
            return parseJSON(response);
        } catch (e) {
            console.error(e);
            // Return mock response as fallback
            return {
                response: `Error connecting to chat service. Mock response for: "${msg}". Please check if the backend is running on http://localhost:8000`,
                agent_id: undefined,
                agent_label: undefined
            };
        }
    }
};

export default ChatAPI;