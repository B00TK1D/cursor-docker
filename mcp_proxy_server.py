#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Any

JSONRPC_VERSION = "2.0"
MCP_VERSION = "2024-11-05"

TRAFFIC_DIR = Path("/var/mitmproxy/traffic")
INDEX_FILE = TRAFFIC_DIR / "index.json"


def log_debug(msg: str):
    """Log debug messages to stderr."""
    print(f"[DEBUG] {msg}", file=sys.stderr)


def clear_traffic():
    """Clear all captured mitmproxy traffic."""
    import shutil
    try:
        if TRAFFIC_DIR.exists():
            for f in TRAFFIC_DIR.glob("*.json"):
                if f.name != "index.json":
                    f.unlink()
        with open(INDEX_FILE, 'w') as f:
            json.dump({"requests": []}, f)
        log_debug("Mitmproxy traffic cleared")
    except Exception as e:
        log_debug(f"Error clearing traffic: {e}")


def read_index() -> dict:
    """Read the traffic index file."""
    if not INDEX_FILE.exists():
        return {"requests": []}
    try:
        with open(INDEX_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"requests": []}


def read_request(request_id: str) -> dict | None:
    """Read a specific request/response by ID."""
    request_file = TRAFFIC_DIR / f"{request_id}.json"
    if not request_file.exists():
        return None
    try:
        with open(request_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def send_response(response: dict):
    """Send a JSON-RPC response."""
    response["jsonrpc"] = JSONRPC_VERSION
    output = json.dumps(response)
    sys.stdout.write(output + "\n")
    sys.stdout.flush()


def handle_initialize(request_id: Any, params: dict) -> dict:
    """Handle the initialize request."""
    return {
        "id": request_id,
        "result": {
            "protocolVersion": MCP_VERSION,
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "mitmproxy-mcp",
                "version": "1.0.0"
            }
        }
    }


def handle_tools_list(request_id: Any) -> dict:
    """Return the list of available tools."""
    tools = [
        {
            "name": "list_requests",
            "description": "List all captured HTTP requests with summary information. Returns request ID, timestamp, method, URL, host, status code, and content sizes. Use the request ID with read_request to get full details.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of requests to return (default: 100, use 0 for all)"
                    },
                    "host_filter": {
                        "type": "string",
                        "description": "Filter requests by host (partial match)"
                    },
                    "method_filter": {
                        "type": "string",
                        "description": "Filter requests by HTTP method (GET, POST, etc.)"
                    },
                    "status_filter": {
                        "type": "integer",
                        "description": "Filter requests by status code"
                    },
                    "url_filter": {
                        "type": "string",
                        "description": "Filter requests by URL (partial match)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "read_request",
            "description": "Read the full details of a specific captured request/response, including all headers and body content. Use list_requests first to get the request ID.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "The unique ID of the request to read (from list_requests)"
                    }
                },
                "required": ["request_id"]
            }
        },
        {
            "name": "search_requests",
            "description": "Search through captured requests by content. Searches both request and response bodies.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find in request/response bodies"
                    },
                    "search_headers": {
                        "type": "boolean",
                        "description": "Also search in headers (default: false)"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "clear_requests",
            "description": "Clear all captured requests. Use with caution - this deletes all stored traffic data.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_request_stats",
            "description": "Get statistics about captured traffic including total requests, requests by host, by method, and by status code.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "export_har",
            "description": "Export captured traffic in HAR (HTTP Archive) format for use with other tools.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "request_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of request IDs to export. If empty, exports all."
                    }
                },
                "required": []
            }
        }
    ]
    return {
        "id": request_id,
        "result": {"tools": tools}
    }


def handle_resources_list(request_id: Any) -> dict:
    """Return the list of available resources."""
    return {
        "id": request_id,
        "result": {"resources": []}
    }


def tool_list_requests(params: dict) -> str:
    """List captured requests with optional filtering."""
    index = read_index()
    requests = index.get("requests", [])

    host_filter = params.get("host_filter", "").lower()
    method_filter = params.get("method_filter", "").upper()
    status_filter = params.get("status_filter")
    url_filter = params.get("url_filter", "").lower()
    limit = params.get("limit", 100)

    filtered = []
    for req in requests:
        if host_filter and host_filter not in req.get("host", "").lower():
            continue
        if method_filter and req.get("method", "").upper() != method_filter:
            continue
        if status_filter and req.get("status_code") != status_filter:
            continue
        if url_filter and url_filter not in req.get("url", "").lower():
            continue
        filtered.append(req)

    if limit > 0:
        filtered = filtered[-limit:]  # Get most recent

    if not filtered:
        return "No requests captured yet. Configure your browser to use the proxy at localhost:8888."

    lines = [f"Found {len(filtered)} captured requests:\n"]
    for req in filtered:
        lines.append(
            f"[{req['id']}] {req['timestamp']}\n"
            f"  {req['method']} {req['url']}\n"
            f"  Status: {req['status_code']} | "
            f"Request: {req.get('request_size', 0)} bytes | "
            f"Response: {req.get('response_size', 0)} bytes\n"
        )

    return "\n".join(lines)


def tool_read_request(params: dict) -> str:
    """Read full details of a specific request."""
    request_id = params.get("request_id")
    if not request_id:
        return "Error: request_id is required"

    data = read_request(request_id)
    if data is None:
        return f"Error: Request with ID '{request_id}' not found"

    req = data["request"]
    resp = data["response"]

    output = []
    output.append(f"=== REQUEST {data['id']} ===")
    output.append(f"Timestamp: {data['timestamp']}")
    output.append("")
    output.append("--- REQUEST ---")
    output.append(f"{req['method']} {req['url']}")
    output.append(f"Host: {req['host']}:{req['port']}")
    output.append(f"Scheme: {req['scheme']}")
    output.append("")
    output.append("Request Headers:")
    for key, value in req["headers"].items():
        output.append(f"  {key}: {value}")
    output.append("")
    if req["content"]:
        output.append(f"Request Body ({req['content_length']} bytes):")
        output.append(req["content"])
    else:
        output.append("Request Body: (empty)")

    output.append("")
    output.append("--- RESPONSE ---")
    output.append(f"Status: {resp['status_code']} {resp['reason']}")
    output.append("")
    output.append("Response Headers:")
    for key, value in resp["headers"].items():
        output.append(f"  {key}: {value}")
    output.append("")
    if resp["content"]:
        output.append(f"Response Body ({resp['content_length']} bytes):")
        content = resp["content"]
        if len(content) > 50000:
            content = content[:50000] + f"\n... [truncated, {len(resp['content'])} total bytes]"
        output.append(content)
    else:
        output.append("Response Body: (empty)")

    return "\n".join(output)


def tool_search_requests(params: dict) -> str:
    """Search through captured requests."""
    query = params.get("query", "").lower()
    search_headers = params.get("search_headers", False)

    if not query:
        return "Error: query is required"

    index = read_index()
    matches = []

    for req_summary in index.get("requests", []):
        data = read_request(req_summary["id"])
        if data is None:
            continue

        found_in = []

        if query in data["request"].get("content", "").lower():
            found_in.append("request body")

        if query in data["response"].get("content", "").lower():
            found_in.append("response body")

        if query in data["request"].get("url", "").lower():
            found_in.append("URL")

        if search_headers:
            for key, value in data["request"].get("headers", {}).items():
                if query in key.lower() or query in str(value).lower():
                    found_in.append("request headers")
                    break
            for key, value in data["response"].get("headers", {}).items():
                if query in key.lower() or query in str(value).lower():
                    found_in.append("response headers")
                    break

        if found_in:
            matches.append({
                "id": req_summary["id"],
                "method": req_summary["method"],
                "url": req_summary["url"],
                "found_in": found_in
            })

    if not matches:
        return f"No requests found matching '{query}'"

    lines = [f"Found {len(matches)} requests matching '{query}':\n"]
    for match in matches:
        lines.append(
            f"[{match['id']}] {match['method']} {match['url']}\n"
            f"  Found in: {', '.join(match['found_in'])}\n"
        )

    return "\n".join(lines)


def tool_clear_requests(params: dict) -> str:
    """Clear all captured requests."""
    clear_traffic()
    return "All captured requests have been cleared."


def tool_get_request_stats(params: dict) -> str:
    """Get statistics about captured traffic."""
    index = read_index()
    requests = index.get("requests", [])

    if not requests:
        return "No requests captured yet."

    total = len(requests)
    by_host = {}
    by_method = {}
    by_status = {}
    total_request_size = 0
    total_response_size = 0

    for req in requests:
        host = req.get("host", "unknown")
        by_host[host] = by_host.get(host, 0) + 1

        method = req.get("method", "unknown")
        by_method[method] = by_method.get(method, 0) + 1

        status = req.get("status_code", 0)
        status_group = f"{status // 100}xx"
        by_status[status_group] = by_status.get(status_group, 0) + 1

        total_request_size += req.get("request_size", 0)
        total_response_size += req.get("response_size", 0)

    lines = [
        f"=== Traffic Statistics ===",
        f"Total Requests: {total}",
        f"Total Request Data: {total_request_size:,} bytes",
        f"Total Response Data: {total_response_size:,} bytes",
        "",
        "By Host (top 10):",
    ]

    for host, count in sorted(by_host.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"  {host}: {count}")

    lines.append("")
    lines.append("By Method:")
    for method, count in sorted(by_method.items(), key=lambda x: -x[1]):
        lines.append(f"  {method}: {count}")

    lines.append("")
    lines.append("By Status Code:")
    for status, count in sorted(by_status.items()):
        lines.append(f"  {status}: {count}")

    return "\n".join(lines)


def tool_export_har(params: dict) -> str:
    """Export traffic in HAR format."""
    request_ids = params.get("request_ids", [])
    index = read_index()

    if not request_ids:
        request_ids = [req["id"] for req in index.get("requests", [])]

    if not request_ids:
        return "No requests to export."

    entries = []
    for req_id in request_ids:
        data = read_request(req_id)
        if data is None:
            continue

        req = data["request"]
        resp = data["response"]

        entry = {
            "startedDateTime": data["timestamp"],
            "request": {
                "method": req["method"],
                "url": req["url"],
                "httpVersion": "HTTP/1.1",
                "headers": [{"name": k, "value": v} for k, v in req["headers"].items()],
                "queryString": [],
                "bodySize": req["content_length"],
                "postData": {
                    "mimeType": req["headers"].get("content-type", ""),
                    "text": req["content"]
                } if req["content"] else None
            },
            "response": {
                "status": resp["status_code"],
                "statusText": resp["reason"],
                "httpVersion": "HTTP/1.1",
                "headers": [{"name": k, "value": v} for k, v in resp["headers"].items()],
                "content": {
                    "size": resp["content_length"],
                    "mimeType": resp["headers"].get("content-type", ""),
                    "text": resp["content"]
                },
                "bodySize": resp["content_length"]
            },
            "cache": {},
            "timings": {"wait": 0, "receive": 0}
        }
        entries.append(entry)

    har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "mitmproxy-mcp", "version": "1.0.0"},
            "entries": entries
        }
    }

    return json.dumps(har, indent=2)




def handle_tool_call(request_id: Any, params: dict) -> dict:
    """Handle a tools/call request."""
    tool_name = params.get("name")
    tool_params = params.get("arguments", {})

    handlers = {
        "list_requests": tool_list_requests,
        "read_request": tool_read_request,
        "search_requests": tool_search_requests,
        "clear_requests": tool_clear_requests,
        "get_request_stats": tool_get_request_stats,
        "export_har": tool_export_har,
    }

    handler = handlers.get(tool_name)
    if handler is None:
        return {
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Unknown tool: {tool_name}"
            }
        }

    try:
        result = handler(tool_params)
        return {
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": result}]
            }
        }
    except Exception as e:
        return {
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


def main():
    TRAFFIC_DIR.mkdir(parents=True, exist_ok=True)

    log_debug("MCP Proxy Server started")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                log_debug(f"JSON decode error: {e}")
                continue

            request_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            log_debug(f"Processing method: {method}")

            if method == "initialize":
                response = handle_initialize(request_id, params)
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                response = handle_tools_list(request_id)
            elif method == "tools/call":
                response = handle_tool_call(request_id, params)
            elif method == "resources/list":
                response = handle_resources_list(request_id)
            else:
                if request_id is None:
                    continue

                response = {
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            send_response(response)
            log_debug(f"Sent response for {method}")

        except Exception as e:
            log_debug(f"Error: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
