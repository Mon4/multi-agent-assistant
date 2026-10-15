import subprocess
import json
import sys
import time

def financial_tool(category: str) -> str:
    """
    Fetches real-time financial data for stocks, crypto, or currencies using MCP server.
    Args:
        category: 'stocks', 'crypto', or 'currencies'.
    """
    urls = {
        "stocks": "https://finance.yahoo.com/markets/stocks/most-active/",
        "crypto": "https://finance.yahoo.com/markets/crypto/all/",
        "currencies": "https://finance.yahoo.com/markets/currencies"
    }
    
    selected_url = urls.get(category.lower())
    if not selected_url:
        return f"Error: Unknown category '{category}'. Available: stocks, crypto, currencies."

    try:
        fake_user_agent = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        process = subprocess.Popen(
            ["docker", "run", "-i", "--rm", "mcp-fetch", '--user-agent', fake_user_agent],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            bufsize=0
        )

        # 3. Handshake (Initialize -> Wait -> Initialized -> Call)
        # A. Initialize
        init_msg = {
            "jsonrpc": "2.0", "id": 0, "method": "initialize", 
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "adk-agent", "version": "1.0"}}
        }
        process.stdin.write(json.dumps(init_msg) + "\n")
        process.stdin.flush()

        # B. Wait (id: 0)
        while True:
            line = process.stdout.readline()
            if not line: break
            try:
                data = json.loads(line)
                if data.get("id") == 0:
                    break # Handshake OK
            except: pass

        # C. Initialized Notification
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        process.stdin.flush()

        # D. Fetch
        fetch_msg = {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call", 
            "params": {"name": "fetch", "arguments": {"url": selected_url}}
        }
        process.stdin.write(json.dumps(fetch_msg) + "\n")
        process.stdin.flush()

        # 4. Get Data (with timeoutem)
        start_wait = time.time()
        final_result = "Error: No data received."
        
        while True:
            if time.time() - start_wait > 20:
                final_result = "Error: Timeout waiting for financial data."
                break

            line = process.stdout.readline()
            if not line: break
            
            try:
                resp = json.loads(line)
                
                # Succes (ID 1)
                if resp.get("id") == 1 and "result" in resp:
                    content = resp["result"].get("content", [])
                    text = "".join([item.get("text", "") for item in content])
                    # cut text
                    final_result = f"Financial Data ({selected_url}):\n{text[:6000]}" 
                    break
                
                # MCP server error
                if resp.get("id") == 1 and "error" in resp:
                    final_result = f"MCP Server Error: {resp['error'].get('message')}"
                    break
                    
            except json.JSONDecodeError:
                continue
        
        process.kill()
        return final_result

    except Exception as e:
        return f"System Error: {str(e)}"