docker build --platform linux/amd64 -t ghcr.io/fhswf/fh-swifty-chatbot:latest .
echo $GITHUB_TOKEN | docker login ghcr.io -u username --password-stdin
docker push ghcr.io/fhswf/fh-swifty-chatbot:latest 