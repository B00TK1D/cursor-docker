#!/bin/sh

mkdir /backup
cp -r . /backup/
chmod -R 111 /backup/

# Check if CURSOR_API_KEY is set
if [ -z "$CURSOR_API_KEY" ]; then
  /root/.local/bin/cursor-agent login
fi
# Create a chat session
CHAT_SESSION_ID=${CHAT_SESSION_ID:-$(/root/.local/bin/cursor-agent create-chat)}
echo "Chat session ID: $CHAT_SESSION_ID"

TIMEOUT=${TIMEOUT:-600}
MODEL=${MODEL:-"auto"}

# Loop over all the files in /prompts, and pass them as commands to cursor-cli
for file in /prompts/*; do
  if [ -f "$file" ]; then
    echo "Processing prompt file: $file"
    timeout $TIMEOUT /root/.local/bin/cursor-agent --force --print --output-format stream-json --approve-mcps --model $MODEL --resume $CHAT_SESSION_ID $(cat "$file") | tee -a /logs/chat.log
  fi
done

/root/.local/bin/cursor-agent --force --approve-mcps --model $MODEL --resume $CHAT_SESSION_ID

echo "Resume chat session ID: $CHAT_SESSION_ID"
