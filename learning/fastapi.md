# FastAPI

## 1. What is it?

FastAPI is a modern, **open‑source** web‑framework for building **APIs** (Application Programming Interfaces) in **Python**.  
It lets you define the shape of the data your endpoints return or receive, and it automatically generates **OpenAPI** documentation and **interactive API docs** (like Swagger UI).  

Think of it as a “recipe book” for your web services: you write a simple description of what each endpoint does, and FastAPI handles the heavy lifting—parsing request bodies, validating data, converting types, and even generating client code.  

Key characteristics:

| Feature | What it means for you |
|---------|-----------------------|
| **Fast** | Built on **Starlette** and **Pydantic**, it’s one of the fastest Python web frameworks available. |
| **Automatic validation** | Uses **type hints** to validate incoming data, reducing bugs. |
| **Interactive docs** | You get a live, searchable UI where you can test endpoints without writing extra code. |
| **Production‑ready** | Supports async/await, middleware, dependency injection, and more. |
| **Pythonic** | Leverages native Python features (type hints, dataclasses, etc.) rather than requiring extra configuration. |

## 2. Why does it matter?

- **Industry demand** – Many companies are moving to **microservices** and **serverless** architectures, where a clean, well‑documented API is crucial. FastAPI is quickly becoming the de‑facto standard for Python‑based APIs.
- **Developer experience** – You write less boilerplate code, get instant feedback via docs, and can rely on the framework to enforce data contracts.
- **Productivity** – Automatic OpenAPI generation means you don’t need to maintain separate documentation files; the docs are always in sync with your code.
- **Scalability** – Built on async/await, it works well with I/O‑bound tasks (e.g., database calls, external HTTP requests) and can handle many concurrent connections.
- **Learning value** – Understanding FastAPI introduces you to core concepts like **dependency injection**, **middleware**, **type‑based validation**, and **OpenAPI**, which are useful in many other frameworks.

## 3. How does it work?

FastAPI works in three high‑level stages:

1. **Define endpoints with decorators**  
   You create functions decorated with `@app.get`, `@app.post`, etc. The decorator tells FastAPI the HTTP method, path, and optional query parameters.

2. **Validate and parse request data**  
   FastAPI uses **Pydantic** models (or type hints) to validate incoming JSON, form data, or query strings. If the data doesn’t match the expected shape, FastAPI returns a clear 422 “Unprocessable Entity” error.

3. **Generate responses automatically**  
   The function returns a Python object (dict, list, Pydantic model, etc.) and FastAPI serializes it to JSON. It also builds an **OpenAPI** spec that powers the interactive docs.

**Under the hood**:  
- **Starlette** handles the low‑level HTTP protocol, routing, and middleware.  
- **Pydantic** performs data validation and conversion.  
- **FastAPI** glues them together, adds dependency injection, and writes the OpenAPI schema.

## 4. Practical Example

Below is a tiny but complete FastAPI service that manages a list of “items”. It demonstrates:

- A **GET** endpoint returning all items.  
- A **POST** endpoint that validates a request body.  
- **Dependency injection** to simulate a database session.  

```python
# main.py
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# -------------------------------------------------
# 1️⃣  Database setup (SQLite in‑memory for demo)
# -------------------------------------------------
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ItemDB(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# -------------------------------------------------
# 2️⃣  Pydantic models (request/response shapes)
# -------------------------------------------------
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class Item(ItemCreate):
    id: int

    class Config:
        orm_mode = True   # allow conversion from SQLAlchemy model

# -------------------------------------------------
# 3️⃣  Dependency that yields a DB session
# -------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------
# 4️⃣  FastAPI app
# -------------------------------------------------
app = FastAPI(title="Simple Item API", version="0.1.0")

@app.get("/items/", response_model=List[Item])
def list_items(db: Session = Depends(get_db)):
    """Return all items."""
    return db.query(ItemDB).all()

@app.post("/items/", response_model=Item, status_code=201)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Create a new item."""
    db_item = ItemDB(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# -------------------------------------------------
# 5️⃣  Run with uvicorn (in terminal):
#    uvicorn main:app --reload
# -------------------------------------------------
```

### What you see

| Section | Purpose |
|---------|---------|
| **Database models** (`ItemDB`) | SQLAlchemy ORM representing the persistent storage. |
| **Pydantic models** (`ItemCreate`, `Item`) | Define the **shape** of request bodies and API responses. |
| **Dependency** (`get_db`) | Supplies a DB session to each endpoint without repeating code. |
| **Endpoints** (`/items/`) | Simple, type‑annotated functions that automatically get validation, documentation, and OpenAPI generation. |

When you run `uvicorn main:app --reload` and open `http://127.0.0.1:8000/docs`, you’ll see an interactive UI where you can test both endpoints, see request/response examples, and even try out the API with a live “Try it out” button.

## 5. Common Mistakes

| Mistake | Why it hurts | How to avoid it |
|---------|--------------|-----------------|
| **Ignoring response models** | FastAPI will still work, but you lose automatic validation, OpenAPI docs, and client code generation. | Always add `response_model=` to `@app.get/@app.post` (or use Pydantic models as return types). |
| **Mixing `Dict` and Pydantic models** | Pydantic’s validation is lost; you may get `Dict` instead of a clean object. | Prefer Pydantic models for request/response bodies; wrap dicts in a model if you must. |
| **Forgetting to close DB sessions** | Connection leaks lead to “too many open files” errors in production. | Use a dependency that yields a session (`try…finally` or context manager). |
| **Using mutable default arguments** (e.g., `def foo(items: List[str] = [])` ) | FastAPI evaluates defaults once, causing surprising shared state across requests. | Use `None` as default and create a new list inside the function: `def foo(items: Optional[List[str]] = None)`. |
| **Over‑relying on `jsonable_encoder`** | It’s handy for non‑Pydantic objects, but it can hide type errors. | Keep data in Pydantic models whenever possible; only fall back to `jsonable_encoder` for complex legacy objects. |
| **Not handling exceptions** | FastAPI will turn unhandled exceptions into 500 errors without helpful messages. | Define custom exception handlers (`@app.exception_handler(...)`) or use `HTTPException` for expected errors. |
| **Writing blocking code in async endpoints** | Even though FastAPI supports async, CPU‑bound work blocks the event loop. | Use `asyncio.to_thread` or offload to a process pool for heavy computation. |

## 6. Engineering Insight

- **Dependency Injection (DI)** – FastAPI’s DI is lightweight but powerful. It lets you share logic (DB sessions, authentication, configuration) across endpoints without passing them manually. This pattern mirrors what you’ll see in larger frameworks (e.g., **FastAPI** → **Starlette** → **ASGI**). Understanding DI early helps you design more modular, testable code.

- **OpenAPI & Code Generation** – The generated OpenAPI spec is not just documentation; it’s a **contract** between client and server. Tools like **FastAPI‑CodeGenerator** or **Swagger Codegen** can turn the spec into client SDKs for multiple languages. Knowing how the spec is built (via `openapi()` and `@app.get("/openapi.json")`) is valuable for integrating with CI/CD pipelines.

- **Async/await Best Practices** – FastAPI runs on **ASGI**, meaning each request is a coroutine. You should make external calls (HTTP, DB) async (`await db.execute(...)` if using async SQLAlchemy) to avoid blocking other requests. However, CPU‑intensive tasks should be off‑loaded.

- **Performance Considerations** – While FastAPI is fast, the biggest overhead often comes from **validation** and **serialization**. Use `pydantic.Config` options like `extra='ignore'` or `allow_population_by_field_name` when you know your API contract is stable. Profile with `pytest-benchmark` or `asgiref`'s `benchmark` utilities if you suspect bottlenecks.

- **Testing** – FastAPI integrates nicely with **pytest** and **httpx**. Write tests that use `TestClient` to simulate requests without running a server. This encourages you to treat your API as a black‑box and write contract‑based tests rather than implementation‑specific ones.

## 7. Practice

### Beginner
1. **Create a new FastAPI app** that has a single GET endpoint `/hello/` which returns `{"message": "world"}`.  
2. Add an OpenAPI documentation view and verify it appears at `/docs`.  
3. Run the app with `uvicorn` and test the endpoint using `curl` or the browser.

### Intermediate
1. Define a Pydantic model `Book` with fields `title: str`, `author: str`, `pages: int`.  
2. Implement a POST endpoint `/books/` that accepts a `Book` object, stores it in a **list** (in‑memory), and returns the same object with an auto‑generated `id: int`.  
3. Add a GET endpoint `/books/{book_id}` that retrieves a single book by its `id`.  
4. Ensure both endpoints have proper response models and produce correct OpenAPI schemas.

### Challenge
1. Build a **todo list API** with CRUD operations (create, read all, read one, update, delete).  
2. Use **SQLAlchemy** with an SQLite database (as shown above) for persistence.  
3. Implement **dependency injection** for authentication: a simple API key header `X-API-Key` that must equal `"secret"`. If missing or wrong, raise an `HTTPException` with a 401 status.  
4. Add **error handling** for “not found” cases (return 404 with a JSON body like `{"detail": "Todo not found"}`).  
5. Write **pytest** tests for each endpoint using `TestClient`.  
6. Finally, generate the OpenAPI spec (`/openapi.json`) and verify that the API key header is documented.

## 8. Key Takeaways

- **FastAPI = Fast + API**: It’s a high‑performance, type‑aware framework that reduces boilerplate.  
- **Type hints → Validation**: Use Python’s type hints (or Pydantic models) to describe request/response shapes; FastAPI validates automatically.  
- **Interactive docs**: OpenAPI (Swagger UI) is generated for free, making testing and client generation trivial.  
- **Dependency injection** lets you share resources (DB sessions, auth) across endpoints cleanly.  
- **Async support**: Write async endpoints and use async DB drivers for better concurrency.  
- **Testing**: Use `TestClient` and `pytest` to verify behavior without running a server.  
- **Avoid common pitfalls**: always define response models, handle exceptions, close resources, and avoid mutable defaults.  

Mastering these concepts will give you a solid foundation for building robust, well‑documented APIs in Python and prepare you for more advanced topics like **GraphQL**, **microservices**, and **serverless** deployments. Happy coding!