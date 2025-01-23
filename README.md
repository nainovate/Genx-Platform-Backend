# Brillius Skill Practice App

The Skill Practice App is divided into two main components: the UI and the Backend APIs.

## Table of Contents
- [Prerequisites](#prerequisites)
- [UI Setup](#ui-setup)
- [UI Configuration](#ui-configuration)
- [Running in Network Host](#running-in-network-host)
- [Credentials](#credentials)
- [Setting Questions](#setting-questions)
- [Backend Installation](#backend-installation)
- [Backend Configuration](#backend-configuration)
- [Running the Backend](#running-the-backend)
- [Run using Docker](#run-using-docker)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Support and Contact](#support-and-contact)

## UI
### Prerequisites

Before you start, make sure you have the following prerequisites installed:

- [Node.js](https://nodejs.org/)
- [Visual Studio Code (VS Code)](https://code.visualstudio.com/) (Optional but highly recommended)
- [Conda](https://conda.io/projects/conda/en/latest/index.html) (Optional but highly recommended)
- [Docker (Linux)](https://www.docker.com/) - Required for Linux systems.
- [Docker Desktop (Windows)](https://www.docker.com/products/docker-desktop) - Required for Windows systems.

### UI Setup

1. Clone the repository 
    ```shell
    git clone https://github.com/KumarBrillius/Brillius_Skill_Practice.git
    ```

2. Open the Command Prompt in VS Code (or your preferred terminal) and create a Conda environment (optional but recommended):
    ```shell
    conda create -n frontend

3. When the conda environment is created, activate it using 
    ```shell
    conda activate frontend
    ```

4. Navigate to the frontend directory

5. Now run
    ```shell
    npm install
    ```
6. After the node_modules are installed in the 'frontend' directory, now run 
    ```shell
    npm run build
    ```
    We can see the build folder createdin the frontend directory

7. Navigate to 'src' directory inside the frontend directory and run 
    ```shell
    node server.js
    ```
8. The console must say "Server is running on 0.0.0.0:3000" which means that the frontend server is up and running

9.  Open your web browser and visit the URL: [localhost:3000](http://localhost:3000)

### UI Configuration

1. Navigate to the 'src' directory located in the 'frontend' directory.
2. Open 'constants' folder and go to the config.json and you can find various configurations including the "API URL". Keep the URL as {Your_device_IP_address}:5001
3. There are various configurations including the sessions, modes, timer duration, destinations etc for setting them according to your convinience
   You can change the logosource and logoalt by keeping the logo in the 'public' directory inside the frontend directory.
   You can set the MaxTabSwitchingCount, FullScreenMode, CutCopyPasteMenu, SkipAll to your convinience.

### Running in network host

After following the above steps to run in a network host. Go to the web browser and visit teh URL {your_system_IP_address}:3000

### Credentials
In the config folder of the project, we can see a register_config.yaml file, You can set the user and admin credentials to start with the   application. Please set the required credentials for the admin and user

1. Now take a different terminal and navigate to the 'backend' directory 
    ```shell
    python registration.py
    ```

### Setting Questions
We have a template for setting the questions in the 'backend' directory which is known as questions.yamltemplate. Follow the template and set the questions in the questions.yaml file in the 'config' directory of the project


## Backend

### Backend Installation

1. Navigate to the `backend` directory.

2. Open a separate Command Prompt in VS Code (or your preferred terminal) and create a Conda environment (optional but recommended):
    ```shell
    conda create -n backend

3. When the conda environment is created, activate it using 
    ```shell
    conda activate backend
    ```
3. Install the required dependencies using the following command:
    ```shell
    pip install -r requirements.txt
    ```
    If that does not work please try 
    ```shell
    pip install -r requirements.txt --user
    ```

4. After setting the questions in the format given and credentials for user and admin your server is now ready to start 

### Configuration

In `config.yaml` API endpoints for LLM (Large Language Model) and STT (Speech To Text) server are taken. Update them based on your requirement.
Please refer the [AI-Accelerators](https://github.com/KumarBrillius/AI-Accelerators.git)

We provide you with the STT and LLM services with the endpoints given with various customizations to select from

### Running the Backend

1. To start the Backend APIs, navigate to the 'backend' directory:
    ```shell
    python directoryAPI.py
    ```

This will launch the backend server.

## Run using Docker

1. Navigate to the project dicrectory and run the following command:
    ```shell
    docker-compose up --build
    ```


### Troubleshooting

#### 1. Missing Dependencies

- **Issue**: You might encounter errors related to missing dependencies during the setup.

- **Solution**:
  - Double-check that you've installed Node.js and Python with the required packages as mentioned in the prerequisites.
  - Make sure you're using the correct version of Node.js and Python.
  - If you're using Conda, ensure that you've activated the appropriate environment.

#### 2. Port Conflicts

- **Issue**: If you see a "Port already in use" error, it means the port specified for your application is already occupied.

- **Solution**:
  - Check if any other application is using the same port (e.g., port 3000 for the frontend). You can change the port in your application's configuration.

#### 3. API Configuration Errors

- **Issue**: If the app is not working correctly, it may be due to incorrect API configurations.

- **Solution**:
  - Review the `config.yaml` file for API endpoint configurations and ensure they are correct.
  - Check if the API endpoints you are using are accessible and responsive.

#### 4. Question Setup

- **Issue**: If questions are not appearing as expected in the app, the issue might be related to the question setup.

- **Solution**:
  - Double-check the format of the questions in the `questions.yaml` file in the `config` directory.
  - Ensure the YAML syntax is correct.

#### 5. Permissions and Privileges

- **Issue**: You might face permission issues when installing packages or running scripts.

- **Solution**:
  - Ensure you have the necessary permissions to install packages and run scripts on your system.
  - If you encounter permission issues, you can try running commands with elevated privileges (e.g., using `sudo` for Linux).

#### 6. Network Issues

- **Issue**: If you can't access the app from a network host, it might be due to network or firewall issues.

- **Solution**:
  - Check your network and firewall settings to allow access to the app.
  - Verify that your server's IP address is accessible from the network.

If you encounter any other issues not mentioned here, consider checking the project's issue tracker on its GitHub repository, as the problem you're facing might have already been reported and resolved by other users or contributors.

Remember that troubleshooting often requires patience and attention to detail. It's also a good practice to keep an eye on error messages, log files, and the developer console in your web browser to gather more information about the problem. If you still can't resolve the issue, don't hesitate to seek help from the project's community or maintainers.


### Contributing

We welcome and appreciate contributions from the community. Whether it's bug fixes, feature enhancements, or documentation improvements, your contributions help make the Brillius Skill Practice App better for everyone.

If you're interested in contributing, please follow these guidelines:

1. **Fork the Repository**: Start by forking the project on GitHub.

2. **Create a Branch**: Create a new branch on your fork for the changes you intend to make. Use a descriptive branch name (e.g., `develop/new-branch`).

3. **Make Changes**: Implement your changes or additions to the codebase. Ensure that your code adheres to coding standards and conventions.

4. **Write Tests**: If your changes include new features or modify existing ones, write tests to ensure that everything works as expected.

5. **Documentation**: If your contribution includes changes to the project's documentation, make sure to update the relevant documentation files.

6. **Commit and Push**: Commit your changes with clear and concise commit messages. Push your changes to your fork on GitHub.

7. **Pull Request**: Open a pull request from your fork to the main repository. Be sure to provide a detailed description of the changes you've made.

8. **Code Review**: Your pull request will be reviewed by project maintainers. Be prepared to address feedback or make necessary changes.

9. **Testing**: Ensure that your changes pass all tests and do not introduce new issues.

10. **Merge**: Once your pull request is approved, it will be merged into the main repository.

11. **Thank You**: Your contribution has been successfully merged! Thank you for helping improve the Brillius Skill Practice App.

Please note that by contributing to this project, you agree to abide by the project's code of conduct and licensing terms. We appreciate your support and look forward to your contributions.

If you have any questions or need assistance during the contribution process, feel free to reach out to us by [opening an issue](https://github.com/KumarBrillius/Brillius_Skill_Practice/issues).

Thank you for contributing to the project.


_Note: Please ensure that you have the necessary permissions and privileges to install packages and run scripts on your system._

Feel free to update this README with more specific instructions or additional details about the Brillius Skill Practice App!
