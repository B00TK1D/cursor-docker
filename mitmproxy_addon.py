"""
Mitmproxy addon that captures HTTP/HTTPS traffic and stores it for the MCP server.
"""
import json
import os
import time
import hashlib
from datetime import datetime
from pathlib import Path
from mitmproxy import http, ctx

# Directory to store captured traffic
TRAFFIC_DIR = Path("/var/mitmproxy/traffic")


class TrafficCapture:
    """Addon to capture and store HTTP traffic for MCP server access."""

    def __init__(self):
        self.traffic_dir = TRAFFIC_DIR
        self.traffic_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.traffic_dir / "index.json"
        self._load_index()

    def _load_index(self):
        """Load existing index or create new one."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.index = {"requests": []}
        else:
            self.index = {"requests": []}

    def _save_index(self):
        """Save the index to disk."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _generate_id(self, flow: http.HTTPFlow) -> str:
        """Generate a unique ID for a request/response pair."""
        unique_str = f"{flow.request.method}{flow.request.pretty_url}{time.time()}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def _get_headers_dict(self, headers) -> dict:
        """Convert headers to a dictionary."""
        return dict(headers)

    def _safe_decode(self, content: bytes, content_type: str = "") -> str:
        """Safely decode bytes to string, handling binary content."""
        if content is None:
            return ""

        # Check if content is likely binary
        binary_types = ['image/', 'audio/', 'video/', 'application/octet-stream',
                       'application/pdf', 'application/zip', 'application/gzip']
        for bt in binary_types:
            if bt in content_type.lower():
                return f"[Binary content: {len(content)} bytes, type: {content_type}]"

        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('latin-1')
            except UnicodeDecodeError:
                return f"[Binary content: {len(content)} bytes]"

    def response(self, flow: http.HTTPFlow):
        """Called when a response is received."""
        if flow.response is None:
            return

        request_id = self._generate_id(flow)
        timestamp = datetime.now().isoformat()

        # Get content types
        req_content_type = flow.request.headers.get("content-type", "")
        resp_content_type = flow.response.headers.get("content-type", "")

        # Build the request data
        request_data = {
            "id": request_id,
            "timestamp": timestamp,
            "request": {
                "method": flow.request.method,
                "url": flow.request.pretty_url,
                "host": flow.request.host,
                "port": flow.request.port,
                "path": flow.request.path,
                "scheme": flow.request.scheme,
                "headers": self._get_headers_dict(flow.request.headers),
                "content": self._safe_decode(flow.request.content, req_content_type),
                "content_length": len(flow.request.content) if flow.request.content else 0,
            },
            "response": {
                "status_code": flow.response.status_code,
                "reason": flow.response.reason,
                "headers": self._get_headers_dict(flow.response.headers),
                "content": self._safe_decode(flow.response.content, resp_content_type),
                "content_length": len(flow.response.content) if flow.response.content else 0,
            }
        }

        # Save the full request/response to a file
        request_file = self.traffic_dir / f"{request_id}.json"
        with open(request_file, 'w') as f:
            json.dump(request_data, f, indent=2)

        # Add to index (summary only)
        index_entry = {
            "id": request_id,
            "timestamp": timestamp,
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "host": flow.request.host,
            "status_code": flow.response.status_code,
            "content_type": resp_content_type,
            "request_size": request_data["request"]["content_length"],
            "response_size": request_data["response"]["content_length"],
        }

        self.index["requests"].append(index_entry)
        self._save_index()

        ctx.log.info(f"Captured: {flow.request.method} {flow.request.pretty_url} -> {flow.response.status_code}")


addons = [TrafficCapture()]
