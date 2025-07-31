FROM mcr.microsoft.com/vscode/devcontainers/python:3.12

# Install pipenv or any other tools you need
RUN pip install --upgrade pip

# Optional: expose the Flask port
EXPOSE 8888

# Create a working directory
WORKDIR /workspace

# Default user (provided by base image)
USER vscode
