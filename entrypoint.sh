#!/bin/sh

mkdir /backup
cp -r . /backup/
chmod -R 111 /backup/

CERT_DIR="/root/.mitmproxy"
MOUNTED_CERT_DIR="/certs"

mkdir -p /var/log/supervisor

if [ -d "$MOUNTED_CERT_DIR" ] && [ "$(ls -A $MOUNTED_CERT_DIR 2>/dev/null)" ]; then
    cp -f "$MOUNTED_CERT_DIR"/* "$CERT_DIR/" 2>/dev/null || true
else
    echo "No existing certificates found, generating new ones..."
    mitmdump --listen-port 18888 --set confdir="$CERT_DIR" &
    MITM_PID=$!
    sleep 3
    kill $MITM_PID 2>/dev/null || true

    if [ -d "$MOUNTED_CERT_DIR" ]; then
        cp -f "$CERT_DIR"/* "$MOUNTED_CERT_DIR/" 2>/dev/null || true
        echo "Certificates copied to $MOUNTED_CERT_DIR"
    fi
fi

/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf >/dev/null 2>&1

if [ -z "$CURSOR_API_KEY" ]; then
  /root/.local/bin/cursor-agent login
fi

if [ -z "$CHAT_SESSION_ID" ]; then
  CHAT_SESSION_ID=$(/root/.local/bin/cursor-agent create-chat)
fi
echo "Chat session ID: $CHAT_SESSION_ID"

TIMEOUT=${TIMEOUT:-600}
MODEL=${MODEL:-"auto"}

for file in /prompts/*; do
  if [ -f "$file" ]; then
    echo "Processing prompt file: $file"
    timeout $TIMEOUT /root/.local/bin/cursor-agent --force --print --output-format stream-json --approve-mcps --model $MODEL --resume $CHAT_SESSION_ID $(cat "$file") | tee -a /logs/chat.log
  fi
done

/root/.local/bin/cursor-agent --force --approve-mcps --model $MODEL --resume $CHAT_SESSION_ID

printf "\033[2A\033[90m  Resume: \033[1;36mcursor $CHAT_SESSION_ID\033[0m\n"
