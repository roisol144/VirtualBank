# Backend for VirtualBank

This is the backend component of the **VirtualBank** project, developed using **Flask** and **PostgreSQL**. The backend handles user management, account creation, and transactions, providing RESTful APIs to interact with the data.

---

## Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Running the Backend](#running-the-backend)
4. [API Endpoints](#api-endpoints)
5. [Authentication](#authentication)
6. [Logging](#logging)
7. [Testing](#testing)

---

## Installation

Ensure that you have **Docker** and **Docker Compose** installed on your system. 

### Steps to run the backend:
1. Clone the repository:
   ```bash
   git clone https://github.com/roisol144/VirtualBank.git
   cd VirtualBank/backend
   ```

2. Set up environment variables:
   - Create a `.env` file in the `backend` directory with the following content:
     ```env
     DATABASE_URL=postgresql://<user>:<password>@db:5432/<dbname>
     SECRET_KEY=<your-secret-key>
     ```

3. Build and run the Docker containers:
   ```bash
   docker compose up --build
   ```

4. The backend should now be accessible at `http://localhost:8000`.

---

## Configuration

The backend is configured using a `.env` file that contains sensitive data like the `SECRET_KEY` for encryption and the `DATABASE_URL` for connecting to PostgreSQL.

Make sure to set up the database connection string properly, which will be used by **SQLAlchemy** to connect to the PostgreSQL database.

---

## Running the Backend

Once the Docker containers are running, the backend will be available on `http://localhost:8000`. You can make HTTP requests to the Flask API to interact with the system.

The backend is primarily intended to be used as an API service for the frontend, which handles user registration, authentication, account management, and more.

---

## API Endpoints

The following are the available API endpoints for the backend:

| Endpoint               | Method | Description                |
|------------------------|--------|----------------------------|
| `/register`            | POST   | Register a new user        |
| `/login`               | POST   | Login and retrieve JWT token|
| `/accounts`            | GET    | Get a list of accounts for a user |
| `/accounts/<id>`       | GET    | Retrieve a specific account by ID |
| `/accounts`            | POST   | Create a new bank account  |
| `/accounts/<id>`       | PUT    | Update a bank account      |
| `/accounts/<id>`       | DELETE | Delete a bank account      |

---

## Authentication

The backend uses **JWT (JSON Web Token)** for authentication. Upon successful login, users receive a token, which must be included in the `Authorization` header for all protected routes.

Example:
```bash
Authorization: Bearer <your-jwt-token>
```

---

## Logging

The backend is equipped with logging middleware to capture API request and response details, as well as errors.

Logs are saved to the console (or a file, depending on configuration), which can help track issues and improve debugging.

---

## Testing

Testing for the backend can be done using **pytest**. Ensure the backend is running and execute the following command to run the tests:

```bash
pytest
```

This will run all the backend tests to ensure that everything works as expected.

---

Let me know if you need further adjustments or additional sections for the backend `README.md`!
