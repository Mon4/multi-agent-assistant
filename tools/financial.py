import json
import queue
import subprocess
import sys
import threading
import time

_REQUEST_TIMEOUT_S = 20

FINANCIAL_URLS = {
    "stocks": "https://finance.yahoo.com/markets/stocks/most-active/",
    "crypto": "https://finance.yahoo.com/markets/crypto/all/",
    "currencies": "https://finance.yahoo.com/markets/currencies",
}


def _read_stdout(process, output_queue: queue.Queue) -> None:
    """Push every stdout line of the MCP server into a queue (runs in a daemon thread)."""
    for line in process.stdout:
        output_queue.put(line)


def _wait_for_response_id(output_queue: queue.Queue, response_id: int, timeout_s: float):
    """Read lines from the queue until a JSON-RPC message with the given id arrives (or timeout)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            line = output_queue.get(timeout=max(0.0, deadline - time.time()))
        except queue.Empty:
            return None
        if not line:
            return None
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if message.get("id") == response_id:
            return message
    return None


def financial_tool(category: str) -> str:
    """
    Fetches real-time financial data for stocks, crypto, or currencies using MCP server.
    Args:
        category: 'stocks', 'crypto', or 'currencies'.
    """
    selected_url = FINANCIAL_URLS.get(category.lower())
    if not selected_url:
        return f"Error: Unknown category '{category}'. Available: stocks, crypto, currencies."

    fake_user_agent = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    try:
        process = subprocess.Popen(
            ["docker", "run", "-i", "--rm", "mcp/fetch-server", '--user-agent', fake_user_agent],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            bufsize=1
        )
    except OSError as exc:
        return f"System Error: Could not start the MCP fetch server (is Docker running?): {exc}"

    output_queue = queue.Queue()
    reader_thread = threading.Thread(target=_read_stdout, args=(process, output_queue), daemon=True)
    reader_thread.start()

    try:
        # A. Initialize
        init_msg = {
            "jsonrpc": "2.0", "id": 0, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "adk-agent", "version": "1.0"}}
        }
        process.stdin.write(json.dumps(init_msg) + "\n")
        process.stdin.flush()

        # B. Wait for the initialize response (with deadline)
        if _wait_for_response_id(output_queue, 0, _REQUEST_TIMEOUT_S) is None:
            return "Error: MCP server did not initialize in time (is Docker running?)."

        # C. Initialized notification
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        process.stdin.flush()

        # D. Fetch
        fetch_msg = {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "fetch", "arguments": {"url": selected_url}}
        }
        process.stdin.write(json.dumps(fetch_msg) + "\n")
        process.stdin.flush()

        # E. Get the result (with deadline)
        response = _wait_for_response_id(output_queue, 1, _REQUEST_TIMEOUT_S)
        if response is None:
            return "Error: Timeout waiting for financial data."

        if "result" in response:
            content = response["result"].get("content", [])
            text = "".join(item.get("text", "") for item in content)
            return f"Financial Data ({selected_url}):\n{text[:6000]}"

        if "error" in response:
            return f"MCP Server Error: {response['error'].get('message')}"

        return "Error: Unexpected MCP server response."
    except Exception as exc:
        return f"System Error: {exc}"
    finally:
        process.kill()