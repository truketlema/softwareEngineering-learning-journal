# Docker for Software Engineers

## 1. What is it?

Docker is a platform that lets you **package an application and all its dependencies into a single, portable unit called a *container***.  
Think of a container as a sealed box that holds everything the software needs to run: the code, runtime, system tools, libraries, and environment variables.  

- **Image** – A blueprint or template for a container. It is immutable and describes everything needed to run the application.  
- **Container** – A running instance of an image. You can start, stop, and move containers around just like any process.  

Docker achieves this by using **Linux namespaces and cgroups** to isolate the container’s filesystem, networking, and process tree from the host system, while still sharing the host’s kernel. This makes containers lightweight and fast to start compared to traditional virtual machines.

## 2. Why does it matter?

Software engineers work on many different machines, operating systems, and environments. Docker solves the “it works on my machine” problem by providing a **consistent development, testing, and production environment**.

| Reason | Impact on Engineering |
|--------|------------------------|
| **Consistency** | The same Docker image runs identically on a developer’s laptop, a CI server, and a cloud VM. |
| **Portability** | Move containers from local development to any cloud provider (AWS, GCP, Azure) without re‑installing dependencies. |
| **Isolation** | Prevent “dependency conflicts” between projects by keeping each app’s environment separate. |
| **Scalability** | Starting many containers is cheap; they share the host kernel, so you can spin up microservices quickly. |
| **CI/CD integration** | Pipelines can build and push Docker images, then deploy them with a single command. |

Because modern software stacks often involve multiple services (e.g., a web API, a database, a cache), Docker becomes the glue that holds them together cleanly.

## 3. How does it work?

1. **Dockerfile** – A text file containing a set of instructions to assemble an image. Each instruction creates a new **layer** (like a snapshot) on top of the previous one.  
   ```Dockerfile
   # Example Dockerfile for a Python Flask app
   FROM python:3.11-slim   # base image
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 5000
   CMD ["python", "app.py"]
   ```
2. **Docker Build** – The Docker daemon reads the Dockerfile, starts from the base image, and applies each layer sequentially, caching intermediate results for speed.  
3. **Docker Image** – The final result of the build: a read‑only filesystem with everything needed to run the app.  
4. **Docker Run** – Creates a **container** from an image, allocates resources, and starts the configured command. The container gets its own isolated view of the filesystem, network, and processes.  

   ```bash
   docker build -t my-flask-app .
   docker run -p 5000:5000 my-flask-app
   ```

5. **Docker Compose** (optional) – A YAML file that defines multi‑container applications. It lets you define services, networks, and volumes in one place.

   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "5000:5000"
       volumes:
         - .:/app
     db:
       image: postgres:15
       environment:
         POSTGRES_USER: user
         POSTGRES_PASSWORD: pass
         POSTGRES_DB: mydb
   ```

## 4. Practical Example

Let’s build a tiny **Python Flask** service that returns a greeting and stores a visit count in a SQLite database (all inside a container).

### 4.1 Application code (`app.py`)

```python
from flask import Flask, jsonify
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', '/data/visit_count.db')

def get_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT count FROM visit_counts WHERE id = 1')
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def increment_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create table if missing
    c.execute('CREATE TABLE IF NOT EXISTS visit_counts (id INTEGER PRIMARY KEY, count INTEGER)')
    c.execute('INSERT OR REPLACE INTO visit_counts (id, count) VALUES (1, COALESCE((SELECT count FROM visit_counts WHERE id = 1), 0) + 1)')
    conn.commit()
    conn.close()

@app.route('/')
def hello():
    increment_count()
    count = get_count()
    return jsonify({'message': 'Hello from Docker!', 'visits': count})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### 4.2 Requirements (`requirements.txt`)

```
flask==3.0.0
```

### 4.3 Dockerfile

```Dockerfile
# Use a slim Python image for a small footprint
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (caches this layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source
COPY . .

# Ensure the data directory exists for SQLite
RUN mkdir -p /data

# Expose the Flask port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
```

### 4.4 Build and run

```bash
# Build the image (may take a minute)
docker build -t flask-visit-counter .

# Run the container, mapping the data directory to the host
docker run -p 5000:5000 -v $(pwd)/data:/data flask-visit-counter
```

Now you can hit `http://localhost:5000` and see a JSON response with an incrementing visit count. The entire environment—Flask, SQLite, and the data directory—is encapsulated inside the container.

## 5. Common Mistakes

| Mistake | Why it hurts | How to avoid it |
|---------|--------------|-----------------|
| **Forgetting `.dockerignore`** | Large files (node_modules, .git) are copied into the image, bloating it and slowing builds. | Create a `.dockerignore` file and list directories/files that should stay out. |
| **Using the latest tag (`FROM python:latest`)** | “Latest” can change unexpectedly, breaking reproducibility. | Pin explicit versions (`python:3.11-slim`). |
| **Running containers as root** | Reduces isolation; a compromised app could affect the host. | Use a non‑root user in the Dockerfile (`RUN useradd -m appuser && USER appuser`). |
| **Not cleaning up cached layers** | Over time, the build cache grows, wasting disk space. | Run `docker builder prune` periodically. |
| **Hard‑coding absolute paths** | Makes the container less portable across hosts. | Use environment variables or `WORKDIR` to keep paths relative. |
| **Ignoring security updates** | Base images may have known vulnerabilities. | Regularly `docker pull <image>` and rebuild. |

## 6. Engineering Insight

- **Multi‑stage builds**: Use multiple `FROM` statements in a Dockerfile to separate the build environment from the runtime. This yields a tiny final image with only the necessary artifacts.  
  ```Dockerfile
  # Stage 1 – build
  FROM python:3.11-slim AS builder
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --user -r requirements.txt

  # Stage 2 – runtime
  FROM python:3.11-slim
  WORKDIR /app
  COPY --from=builder /root/.local /usr/local
  COPY . .
  CMD ["python", "app.py"]
  ```
- **Resource limits**: Use `--cpus`, `--memory`, and `--pids-limit` flags or Docker Compose’s `deploy.resources` to prevent a single container from starving the host.  
- **Networking**: Docker creates an isolated bridge network. For microservices, you can connect containers via service names (e.g., `db`) without exposing ports.  
- **Orchestration**: Docker Swarm and Kubernetes build on Docker to manage large clusters. Understanding Docker images and containers is the first step toward using these tools.  
- **Testing strategy**: Write automated tests that run inside a container (e.g., using Docker’s `docker run --rm <image> pytest`). This ensures your tests run in the same environment as production.

## 7. Practice

### Beginner
1. Pull the official `nginx` image and run it so it serves a default page on port 80.  
2. Verify you can reach the page from your host (`curl http://localhost`).  
3. Stop the container and remove it.

### Intermediate
1. Create a simple Python Flask app that reads an environment variable `MESSAGE` and returns it.  
2. Write a Dockerfile that uses a multi‑stage build to keep the final image small.  
3. Build the image, run it with a custom `MESSAGE`, and test with `curl`.

### Challenge
Design a small **microservice architecture** using Docker Compose:

- **Web service** – a Flask app that stores a counter in Redis.  
- **Redis service** – for fast key‑value storage.  
- **Database service** – a PostgreSQL container for persistent logs.  

Requirements:

- Use environment files (`.env`) for secrets.  
- Add health‑check endpoints to each service.  
- Write a simple CI script (e.g., a GitHub Actions workflow) that runs `docker compose build` and `docker compose up --wait` before running integration tests.  

Submit the `docker‑compose.yml`, `.env`, and the CI workflow file.

## 8. Key Takeaways

- **Docker packages code + dependencies** into portable, isolated containers.  
- A **Dockerfile** defines an immutable **image**; a **container** is a running instance.  
- Use **`.dockerignore`**, pin image tags, and keep images small for reliable builds.  
- Leverage **multi‑stage builds**, resource limits, and health checks for production‑grade containers.  
- Docker is the foundation for modern **CI/CD**, **microservices**, and **orchestration** tools.  

With these concepts and hands‑on practice, you’ll be ready to incorporate Docker into any software engineering workflow. Happy containerizing!