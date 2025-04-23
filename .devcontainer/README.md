# Development Container for Genx-Platform-Backend

This directory contains configuration files for setting up a development container for the Genx-Platform-Backend project using Visual Studio Code's Remote - Containers extension.

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop) installed on your machine
- [Visual Studio Code](https://code.visualstudio.com/) installed on your machine
- [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed in VS Code

## Getting Started

1. Open the project folder in VS Code
2. VS Code will detect the dev container configuration and prompt you to reopen the project in a container. Click "Reopen in Container"
3. Alternatively, you can click on the green icon in the bottom-left corner of VS Code and select "Remote-Containers: Reopen in Container"
4. VS Code will build the container and set up the development environment (this may take a few minutes the first time)
5. Once the container is built, you can start developing!

## Features

- Python 3.11 environment with all required dependencies installed
- Qt development libraries (qtbase5-dev, qt5-qmake, qttools5-dev-tools, libqt5webkit5-dev, libsip-dev) for PyQt5 support
- PyQt5 pre-installed in the container to avoid memory issues during container startup
- Memory limits configured (4GB) to handle resource-intensive package installations
- Development tools: black, flake8, pytest
- VS Code extensions for Python development
- Port forwarding for the FastAPI application (5000, 5001)
- Environment variables pre-configured for development

## Running the Application

Once inside the dev container, you can run the application with:

```bash
cd AIPlatform_backend
python main.py
```

The application will be available at http://localhost:5000

## MongoDB Connection

By default, the dev container is configured to connect to MongoDB on the host machine. If you want to run MongoDB inside the container:

1. Uncomment the MongoDB service in `.devcontainer/docker-compose.yml`
2. Update the environment variables in `.devcontainer/docker-compose.yml` to use `mongodb` as the MongoDB host
3. Rebuild the container (Command Palette > Remote-Containers: Rebuild Container)

## Customizing the Dev Container

You can customize the dev container by modifying the following files:

- `.devcontainer/Dockerfile`: Change the base image, install additional system packages, etc.
- `.devcontainer/devcontainer.json`: Configure VS Code settings, extensions, etc.
- `.devcontainer/docker-compose.yml`: Add additional services, volumes, etc.
