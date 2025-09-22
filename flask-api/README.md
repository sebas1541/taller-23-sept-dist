# Flask HR API

A simple Flask API for managing HR data (Employees and Departments) using Neo4j as the database.

## Features

- **Health Check**: `/health` endpoint for monitoring
- **Employee Management**: CRUD operations for employees
- **Department Management**: CRUD operations for departments
- **Load Balancing Support**: Returns container hostname in responses
- **Neo4j Integration**: Uses Neo4j graph database for data storage

## API Endpoints

### Health & Info
- `GET /health` - Health check endpoint
- `GET /` - API information and available endpoints

### Employees
- `GET /employees` - List all employees
- `POST /employees` - Create a new employee
- `GET /employees/<id>` - Get employee by ID

### Departments
- `GET /departments` - List all departments
- `POST /departments` - Create a new department
- `GET /departments/<id>` - Get department by ID

## Data Schema

### Employee
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "position": "string",
  "created_at": "datetime",
  "department_id": "uuid (optional)"
}
```

### Department
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string (optional)",
  "created_at": "datetime"
}
```

## Neo4j Graph Model

The API creates the following Neo4j structure:
- **Employee** nodes with properties: id, name, email, position, created_at
- **Department** nodes with properties: id, name, description, created_at
- **WORKS_IN** relationship connecting employees to departments

## Environment Variables

Copy `.env.example` to `.env` and adjust the values:

```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
PORT=5000
```

## Running Locally

```bash
pip install -r requirements.txt
python app.py
```

## Docker

```bash
docker build -t flask-hr-api .
docker run -p 5000:5000 \
  -e NEO4J_URI=bolt://neo4j:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=password \
  flask-hr-api
```

## Example Requests

### Create Department
```bash
curl -X POST http://localhost:5000/departments \
  -H "Content-Type: application/json" \
  -d '{"name": "Engineering", "description": "Software Development Team"}'
```

### Create Employee
```bash
curl -X POST http://localhost:5000/employees \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@company.com", "position": "Software Engineer", "department_id": "dept-uuid"}'
```

### List Employees
```bash
curl http://localhost:5000/employees
```

## Notes for Traefik Integration

- The API includes hostname in responses for load balancing demonstration
- Health check endpoint is available at `/health`
- All endpoints return JSON responses with proper HTTP status codes
- Error handling includes custom 404 and 500 error responses