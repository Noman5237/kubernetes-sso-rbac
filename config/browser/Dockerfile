FROM node:22-bookworm-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392
USER root
RUN apt-get update && apt-get install -y --no-install-recommends chromium libnss3-tools ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/lab-browser
RUN npm install --save-exact playwright@1.58.2
ENV NODE_PATH=/opt/lab-browser/node_modules
