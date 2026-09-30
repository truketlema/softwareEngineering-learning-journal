# REST APIs

## 1. What is it?

A REST API (Representational State Transfer Application Programming Interface) is a set of rules and conventions for building and interacting with web services. It allows different software applications to communicate with each other over the internet using standard HTTP methods (GET, POST, PUT, DELETE).

In simpler terms, think of an API as a waiter in a restaurant. You (the client) tell the waiter what you want, the waiter takes your request to the kitchen (the server), and then brings back your food. REST APIs work similarly - your application sends a request to a server, and the server sends back a response.

## 2. Why does it matter?

Understanding REST APIs is crucial for software engineers because:

- **Interoperability**: Different systems (web, mobile, IoT) can communicate seamlessly
- **Scalability**: REST allows stateless communication, making systems more scalable
- **Standardization**: Uses standard HTTP methods and status codes that most developers know
- **Flexibility**: Supports various data formats (JSON, XML, etc.)
- **Industry standard**: Most modern web services use REST APIs

You'll encounter REST APIs in virtually every software project - from social media integrations to payment processing, weather services to enterprise applications.

## 3. How does it work?

REST APIs operate on these key principles:

**HTTP Methods**: Each request specifies an action:
- GET: Retrieve data
- POST: Create new data
- PUT/PATCH: Update existing data
- DELETE: Remove data

**Endpoints**: URLs that represent resources (e.g., `/api/users`, `/api/products`)

**Statelessness**: Each request contains all necessary information - the server doesn't store client state

**HTTP Status Codes**: Responses include status codes that indicate success or failure:
- 200 OK: Success
- 201 Created: Resource created
- 400 Bad Request: Invalid request
- 404 Not Found: Resource doesn't exist
- 500 Internal Server Error: Server problem

**Data Format**: Typically JSON (JavaScript Object Notation)

Example flow:
1. Client sends HTTP request to endpoint
2. Server processes request
3. Server returns HTTP response with status code and data
4. Client handles the response

## 4. Practical Example

Let's build a simple REST API for a book collection using Python and Flask:

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

# Mock database
books = [
    {"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"id": 2, "title": "1984", "author": "George Orwell"}
]

# GET all books
@app.route('/api/books', methods=['GET'])
def get_books():
    return jsonify(books)

# GET single book by ID
@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = next((b for b in books if b['id'] == book_id), None)
    if book:
        return jsonify(book)
    return jsonify({"error": "Book not found"}), 404

# POST create new book
@app.route('/api/books', methods=['POST'])
def create_book():
    if not request.json or not 'title' in request.json or not 'author' in request.json:
        return jsonify({"error": "Missing required fields: title, author"}), 400
    
    new_book = {
        "id": len(books) + 1,
        "title": request.json['title'],
        "author": request.json['author']
    }
    books.append(new_book)
    return jsonify(new_book), 201

# DELETE a book
@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    global books
    books = [b for b in books if b['id'] != book_id]
    return jsonify({"result": "Book deleted"})

if __name__ == '__main__':
    app.run(debug=True)
```

**Testing the API:**

```python
import requests

# Get all books
response = requests.get('http://localhost:5000/api/books')
print(response.json())

# Add a new book
new_book = {"title": "To Kill a Mockingbird", "author": "Harper Lee"}
response = requests.post('http://localhost:5000/api/books', json=new_book)
print(response.json())
```

## 5. Common Mistakes

**1. Ignoring HTTP Status Codes**
- Mistake: Returning 200 for errors
- Fix: Use appropriate status codes (404 for not found, 400 for bad request, etc.)

**2. Over-engineering Endpoints**
- Mistake: Creating overly complex URLs
- Fix: Keep endpoints simple and resource-focused

**3. Not Handling Errors Properly**
- Mistake: Crashing on invalid input
- Fix: Validate input and return meaningful error messages

**4. Ignoring Security**
- Mistake: Exposing sensitive data
- Fix: Use authentication and sanitize inputs

**5. Inconsistent Data Formats**
- Mistake: Mixing JSON and XML without reason
- Fix: Choose one format and stick to it

## 6. Engineering Insight

**Versioning**: APIs change over time. Implement versioning (e.g., `/api/v1/books`) to maintain backward compatibility.

**Pagination**: For large datasets, always implement pagination to prevent overwhelming responses:
```python
page = request.args.get('page', 1, type=int)
per_page = request.args.get('per_page', 10, type=int)
start = (page - 1) * per_page
end = start + per_page
return jsonify(books[start:end])
```

**Rate Limiting**: Protect your API from abuse by limiting how many requests a client can make.

**Caching**: Use HTTP headers like `Cache-Control` to improve performance.

**Documentation**: Always document your API using tools like Swagger/OpenAPI.

**Testing**: Write integration tests that test your API endpoints thoroughly.

## 7. Practice

### Beginner Exercise
Create a simple "Todo List" API with these endpoints:
- GET `/api/todos` - Get all todos
- GET `/api/todos/<id>` - Get a specific todo
- POST `/api/todos` - Create a new todo
- PUT `/api/todos/<id>` - Update a todo
- DELETE `/api/todos/<id>` - Delete a todo

### Intermediate Exercise
Enhance your Todo API with:
- User authentication (use JWT tokens)
- Task categories
- Due dates
- Status tracking (pending, completed)

### Challenge Exercise
Build a REST API for a library system with:
- Book management (add, update, delete books)
- Member management
- Book borrowing/returning system
- Search functionality by title, author, or genre
- Overdue book tracking
- Implement proper error handling and validation

## 8. Key Takeaways

1. REST APIs enable communication between different software systems
2. Use standard HTTP methods (GET, POST, PUT, DELETE) for CRUD operations
3. Always return appropriate HTTP status codes
4. Keep endpoints resource-oriented and simple
5. Implement proper error handling and validation
6. Consider performance aspects like pagination and caching
7. Document your API and write comprehensive tests
8. Plan for versioning and security from the beginning
9. Use JSON as the primary data format
10. Practice building and consuming REST APIs regularly