# Docker

## 1. What is it?
Docker is a platform that lets you package applications into **containers**—standardized, executable units that bundle your code with everything it needs to run: libraries, system tools, settings, and dependencies.

Think of a container as a lightweight, isolated sandbox. Unlike a virtual machine, a container shares the host operating system's kernel but keeps processes, files, and network interfaces separate. This makes containers start in seconds and use megabytes instead of gigabytes.

Key terms:
- **Container**: A running instance of an image. It is ephemeral—when you stop it, its filesystem changes disappear unless you use volumes.
- **Image**: A read-only template used to create containers. Like a class in object-oriented programming, a container is an instance of an image.
- **Docker Engine**: The background service (daemon) that builds images and runs containers.
- **Registry**: A store for images (e.g., Docker Hub, AWS ECR).

## 2. Why does it matter?
Software engineering is a team sport, and environments are the biggest source of friction. Without Docker, you have fought the "works on my machine" bug: code passes on your laptop but fails in staging because of different OS versions, library conflicts, or missing system utilities.

Docker matters because:
- **Consistency**: Dev, CI, and production run identical environments.
- **Isolation**: One machine can safely run multiple conflicting versions of software.
- **Portability**: An image built on macOS runs unchanged on Linux servers in the cloud.
- **Scalability**: Orchestrators like Kubernetes spin up identical containers to handle load.

You will encounter Docker in almost every modern backend, data engineering, and DevOps role.

## 3. How does it work?
The workflow follows a simple pipeline:

1. **Write a Dockerfile**: Text instructions describing the environment.
2. **Build**: `docker build` reads the Dockerfile and creates an image using a union filesystem. Each instruction (`RUN`, `COPY`) creates a cached **layer**. If you change only the last step, Docker reuses previous layers—this is why order matters.
3. **Run**: `docker run` starts a container from the image with its own filesystem, network, and process tree.
4. **Publish**: Push the image to a registry so others or production servers can pull it.

Under the hood, Docker uses Linux namespaces (isolation) and cgroups (resource limits) to sandbox processes without a full OS per app.

## 4. Practical Example
Here is a realistic scenario: containerizing a Python Flask API.

**app.py**
```python
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    name = os.getenv('APP_NAME', 'World')
    return f'Hello, {name}!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**requirements.txt**
```
flask==3.0.0
```

**Dockerfile**
```dockerfile
# Use a slim base image to keep size small
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Document the port the app listens on
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t greeting-api .
docker run -p 5000:5000 -e APP_NAME=Engineer greeting-api
```

Visit `http://localhost:5000` and you should see `Hello, Engineer!`.

## 5. Common Mistakes
- **Running as root**: Containers default to root. If an attacker escapes the sandbox, they own the host. Fix: add `USER 1000` to your Dockerfile.
- **No `.dockerignore`**: Copying `.git`, `__pycache__`, or `node_modules` inflates images and leaks secrets. Always create a `.dockerignore` file.
- **Data in container filesystem**: Databases inside containers lose data on restart. Use named volumes (`-v mydata:/var/lib/db`) or bind mounts for persistence.
- **Huge base images**: `python:3.11` is ~1 GB; `python:3.11-slim` or `python:3.11-alpine` are far smaller.
- **Hardcoding secrets**: Never put API keys in a Dockerfile or image. Use runtime environment variables or a secrets manager.
- **Ignoring health checks**: A container can be "running" while its application is stuck. Add `HEALTHCHECK` instructions for orchestrators.

## 6. Engineering Insight
Docker shifts infrastructure from **mutable servers** to **immutable artifacts**. Instead of SSH-ing into a machine and `apt-get install`-ing packages, you build a new image and redeploy. This makes rollbacks trivial and auditing easier.

Two deeper lessons:
- **Layer caching strategy**: Place infrequently changing instructions (like installing system packages) before frequently changing ones (like copying source code). This speeds up CI builds from minutes to seconds.
- **Single responsibility**: One container should run one process. If your app needs Redis and PostgreSQL, use Docker Compose to link separate containers, not one mega-container.

## 7. Practice
**Beginner**: Write a Dockerfile for a Python script that reads an environment variable `USER_NAME` and prints `Hello, <name>`. Run it with `docker run -e USER_NAME=Alice my-script`.

**Intermediate**: Use Docker Compose to spin up the Flask app from the example alongside a Redis container. The app should increment a visit counter in Redis on each request and display it.

**Challenge**: Refactor the Flask example into a **multi-stage build**. Use a full Python image to install build dependencies (e.g., gcc for compiling packages), then copy only the installed libraries and code into a fresh slim image. Aim for a final image under 120 MB.

## 8. Key Takeaways
- Containers package code + dependencies for consistent, portable execution.
- Images are immutable blueprints; containers are running instances.
- Dockerfiles define reproducible builds; layer order affects cache and speed.
- Use slim bases, non-root users, volumes for data, and `.dockerignore`.
- Docker is the foundation of modern cloud-native development and CI/CD pipelines.