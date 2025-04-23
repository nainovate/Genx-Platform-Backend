# Genx-Platform-Backend

This is the backend for the Genx AI Platform.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Development Container](#development-container)
- [Manual Setup](#manual-setup)
- [Running the Backend](#running-the-backend)
- [Run using Docker](#run-using-docker)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Prerequisites

Before you start, make sure you have the following prerequisites installed:

- [Visual Studio Code (VS Code)](https://code.visualstudio.com/)
- [Docker](https://www.docker.com/products/docker-desktop)
- [VS Code Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

## Development Container

This project includes a development container configuration that sets up a complete development environment with all the necessary dependencies. This is the recommended way to work with this project.

### Using the Dev Container

1. Open the project folder in VS Code
2. VS Code will detect the dev container configuration and prompt you to reopen the project in a container. Click "Reopen in Container"
3. Alternatively, you can click on the green icon in the bottom-left corner of VS Code and select "Remote-Containers: Reopen in Container"
4. VS Code will build the container and set up the development environment (this may take a few minutes the first time)
5. Once the container is built, you can start developing!

For more details about the dev container, see the [.devcontainer/README.md](.devcontainer/README.md) file.

## Manual Setup

If you prefer not to use the dev container, you can set up the project manually:

1. Create a Python virtual environment:
   ```shell
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```shell
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```shell
     source venv/bin/activate
     ```

3. Install the required dependencies:
   ```shell
   pip install -r AIPlatform_backend/requirements.txt
   ```

4. Install the package in development mode:
   ```shell
   pip install -e AIPlatform_backend
   ```

5. Set up environment variables by copying the example file:
   ```shell
   cp AIPlatform_backend/.env.example AIPlatform_backend/.env
   ```
   
6. Edit the `.env` file to configure your environment variables.

## Running the Backend

To start the backend server:

```shell
cd AIPlatform_backend
python main.py
```

This will launch the FastAPI server on port 5000.

## Run using Docker

You can also run the project using Docker Compose:

```shell
docker-compose up --build
```

This will build and start the backend service as defined in the `docker-compose.yml` file.

## Project Structure

- `AIPlatform_backend/`: Main application package
  - `AiManagement/`: AI model management and operations
  - `ApplicationManagment/`: Application business logic
  - `ApplicationRoutes/`: API routes and endpoints
  - `Database/`: Database connections and models
  - `UserManagment/`: User authentication and authorization
  - `main.py`: Application entry point


## Troubleshooting

### 1. MongoDB Connection Issues

- **Issue**: You might encounter errors related to MongoDB connection.

- **Solution**:
  - Ensure MongoDB is running and accessible at the IP address specified in your `.env` file.
  - Check if the MongoDB port is open and not blocked by a firewall.
  - If using the dev container, make sure the MongoDB host is correctly set to `host.docker.internal` or the appropriate service name.

### 2. Port Conflicts

- **Issue**: If you see a "Port already in use" error, it means the port specified for your application is already occupied.

- **Solution**:
  - Check if any other application is using the same port (e.g., port 5000 or 5001).
  - You can change the port in `main.py` or in the Docker configuration.

### 3. Environment Variables

- **Issue**: The application might not work correctly due to missing or incorrect environment variables.

- **Solution**:
  - Ensure all required environment variables are set in your `.env` file.
  - If using Docker, check that the environment variables are correctly passed to the container.
  - In the dev container, environment variables are set in the `devcontainer.json` file.

### 4. Dependencies Installation

- **Issue**: You might face issues with installing dependencies.

- **Solution**:
  - Ensure you're using Python 3.8+ which is compatible with the dependencies.
  - If using pip, try updating pip first: `pip install --upgrade pip`.
  - If a specific package fails to install, check if it requires additional system libraries.

### 5. Dev Container Issues

- **Issue**: Problems with the development container setup.

- **Solution**:
  - Ensure Docker is running before attempting to open the project in a container.
  - Check the Docker logs for any errors during container build.
  - Try rebuilding the container: Command Palette > Remote-Containers: Rebuild Container.
  - Make sure the VS Code Remote - Containers extension is installed and up to date.

### 6. PyQt5 Installation Issues

- **Issue**: Errors related to missing qmake when installing PyQt5 or memory exhaustion during installation.

- **Solution**:
  - The development container has been configured with Qt development libraries (qtbase5-dev, qt5-qmake, qttools5-dev-tools, libqt5webkit5-dev, libsip-dev) to support PyQt5.
  - PyQt5 is now pre-installed in the Docker container to avoid memory issues during container startup.
  - If you're experiencing memory exhaustion during PyQt5 installation, the container has been configured with increased memory limits (4GB).
  - If you're still experiencing issues, rebuild your development container: Command Palette > Remote-Containers: Rebuild Container.
  - If you're setting up manually, install the Qt development libraries:
    - On Ubuntu/Debian: `sudo apt-get install qtbase5-dev qt5-qmake qttools5-dev-tools libqt5webkit5-dev libsip-dev`
    - On macOS: `brew install qt@5`
    - On Windows: Install Qt from the [official website](https://www.qt.io/download) or use `pip install PyQt5-Qt5`


## Contributing

We welcome contributions to the Genx-Platform-Backend project! Here's how you can contribute:

1. **Fork the Repository**: Start by forking the project on GitHub.

2. **Create a Branch**: Create a new branch for your changes with a descriptive name (e.g., `feature/new-api-endpoint` or `fix/mongodb-connection`).

3. **Development Environment**: Use the provided dev container for a consistent development environment.

4. **Code Style**: Follow the existing code style and conventions in the project.

5. **Write Tests**: Add tests for new features or bug fixes to ensure they work as expected.

6. **Documentation**: Update documentation to reflect your changes, including docstrings and README updates.

7. **Commit Messages**: Write clear, concise commit messages that explain your changes.

8. **Pull Request**: Submit a pull request with a clear description of the changes and any relevant issue numbers.

9. **Code Review**: Be open to feedback and be prepared to make changes to your pull request.

Thank you for contributing to the Genx-Platform-Backend project!
