# cursor-docker
Docker container for cursor with built-in HTTP proxy and MCP server for traffic capture.


## Build

```bash
docker build -t cursor-docker .
```
## Install

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
cursor() {
  docker run --rm -it -v $(pwd):/working -v ~/.cursor/certs:/certs -v ~/.cursor/chats:/root/.cursor/chats -p 8888:8888 -e CURSOR_API_KEY=$CURSOR_API_KEY -e CHAT_SESSION_ID="$1" cursor-docker
}
```

## Usage

**Create a new session:**
```bash
cursor
```

**Resume a past session:**
```bash
cursor <session_id>
```


## Manual Run Instructions

```bash
docker run --rm -it \
  -v $(pwd):/working \
  -v ~/.cursor/certs:/certs \
  -p 8888:8888 \
  -e CURSOR_API_KEY=$CURSOR_API_KEY \
  cursor-docker
```

### Browser Setup

1. **Configure proxy**: Set browser HTTP/HTTPS proxy to `localhost:8888`

2. **Install CA certificate** (for HTTPS traffic):
   - Certificate generated automatically on first run at `~/.cursor/certs/mitmproxy-ca-cert.pem`
   - Import the certificate:
     - **Chrome**: Settings → Privacy and Security → Security → Manage certificates → Authorities → Import
     - **Firefox**: Settings → Privacy & Security → Certificates → View Certificates → Authorities → Import
     - **macOS**: Double-click the .pem file, add to Keychain, then trust it for SSL
     - **Linux**: Copy to `/usr/local/share/ca-certificates/` and run `update-ca-certificates`

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_requests` | List all captured HTTP requests with filters (by host, method, status, URL) |
| `read_request` | Read full details of a specific request/response including headers and body |
| `search_requests` | Search through captured requests by content |
| `get_request_stats` | Get statistics about captured traffic |
| `clear_requests` | Clear all captured traffic data |
| `export_har` | Export traffic in HAR format for use with other tools |


