# cursor-docker
Docker container for cursor

Build:
```bash
docker build -t cursor-docker .
```

Install:
```bash
echo "alias cursor='docker run --rm -it -v $(pwd):/working -e CURSOR_API_KEY=$CURSOR_API_KEY cursor-docker'" >> ~/.bashrc
source ~/.bashrc
```
