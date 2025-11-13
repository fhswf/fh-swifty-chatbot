// Set MCP server configuration in local storage
(function() {
    const targetUrl = "https://mcp.fh-swf.cloud/mcp";
    const newServer = {
        "name": "FH SWF MCP Server",
        "clientType": "streamable-http",
        "command": null,
        "url": targetUrl,
        "headers": null,
        "status": "connected"
    };
    
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
        
        // Check if server with target URL already exists
        const serverExists = mcpConfig.some(server => server.url === targetUrl);
        
        if (!serverExists) {
            // Add the new server to the list
            mcpConfig.unshift(newServer);
            localStorage.setItem('mcp_storage_key', JSON.stringify(mcpConfig));
            console.log('[MCP Config] Added FH SWF MCP Server to existing configuration');
        } else {
            console.log('[MCP Config] Server with URL', targetUrl, 'already exists in configuration');
        }
    } catch (error) {
        console.error('[MCP Config] Failed to set MCP storage key:', error);
    }
})();

