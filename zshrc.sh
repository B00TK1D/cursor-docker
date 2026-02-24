cur() {
  export CURSOR_API_KEY=${1:-$CURSOR_API_KEY}
  docker run --rm -it -v $(pwd):/working -v ~/.cursor/certs:/certs -v ~/.cursor/chats:/root/.cursor/chats -v /var/run/docker.sock:/var/run/docker.sock --network host --cap-add=NET_ADMIN -e CURSOR_API_KEY=$CURSOR_API_KEY -e CHAT_SESSION_ID="$2" cursor-docker
}
