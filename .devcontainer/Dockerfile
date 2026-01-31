FROM mcr.microsoft.com/vscode/devcontainers/python:3.13

# Fix Yarn repository GPG key issue that prevents apt-get update
# The base image has Yarn repo configured but with a broken/missing GPG key
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
