// Set MCP server configuration in local storage
(function() {
    const servers = [
        {
            "name": "FH SWF MCP Server",
            "clientType": "streamable-http",
            "command": null,
            "url": "https://mcp.fh-swf.cloud/mcp",
            "headers": null,
            "status": "connected"
        },
        {
            "name": "FH SWF Chatbot MCP Server Internal",
            "clientType": "streamable-http",
            "command": null,
            "url": "http://fh-swifty-mcp-server/mcp",
            "headers": null,
            "status": "connected"
        },
        {
            "name": "FH SWF Chatbot MCP Server External",
            "clientType": "streamable-http",
            "command": null,
            "url": "https://chatbot.fh-swf.cloud/mcp",
            "headers": null,
            "status": "connected"
        }
    ];
    
    try {
        // Check if mcp_storage_key exists in localStorage
        const existingData = localStorage.getItem('mcp_storage_key');
        let mcpConfig = [];
        
        if (existingData) {
            try {
                mcpConfig = JSON.parse(existingData);
                // Check if it's an array, if not, initialize as empty array
                if (!Array.isArray(mcpConfig)) {
                    mcpConfig = [];
                }
            } catch (parseError) {
                console.warn('[MCP Config] Failed to parse existing data, initializing new array:', parseError);
                mcpConfig = [];
            }
        }
        
        // Add each server if it doesn't already exist
        servers.forEach(newServer => {
            const serverExists = mcpConfig.some(server => server.url === newServer.url);
            
            if (!serverExists) {
                // Add the new server to the list
                mcpConfig.unshift(newServer);
                console.log('[MCP Config] Added', newServer.name, 'to existing configuration');
            } else {
                console.log('[MCP Config] Server with URL', newServer.url, 'already exists in configuration');
            }
        });
        
        // Save the updated configuration
        localStorage.setItem('mcp_storage_key', JSON.stringify(mcpConfig));
    } catch (error) {
        console.error('[MCP Config] Failed to set MCP storage key:', error);
    }
})();

