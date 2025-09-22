import os
import socket
from flask import Flask, request, jsonify
from neo4j import GraphDatabase
from datetime import datetime

app = Flask(__name__)

# Neo4j Configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

# Initialize Neo4j driver
driver = None

def init_neo4j():
    global driver
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # Test connection and create constraints/indexes
        with driver.session() as session:
            # Create constraints for unique properties
            session.run("CREATE CONSTRAINT employee_id IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE")
            session.run("CREATE CONSTRAINT department_id IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE")
            
            print("Connected to Neo4j successfully")
            
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        driver = None

def get_hostname():
    """Get container hostname for load balancing demonstration"""
    return socket.gethostname()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'hostname': get_hostname(),
        'neo4j_status': 'connected' if driver else 'disconnected'
    }), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'HR API - Flask',
        'version': '1.0.0',
        'hostname': get_hostname(),
        'endpoints': {
            'health': '/health',
            'employees': {
                'list': 'GET /employees',
                'create': 'POST /employees',
                'get': 'GET /employees/<id>'
            },
            'departments': {
                'list': 'GET /departments',
                'create': 'POST /departments',
                'get': 'GET /departments/<id>'
            }
        }
    }), 200

@app.route('/employees', methods=['GET'])
def get_employees():
    """List all employees"""
    if not driver:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (e:Employee)
                OPTIONAL MATCH (e)-[:WORKS_IN]->(d:Department)
                RETURN e.id as id, e.name as name, e.email as email, 
                       e.position as position, e.created_at as created_at,
                       d.name as department_name
                ORDER BY e.name
            """)
            
            employees = []
            for record in result:
                employee = {
                    'id': record['id'],
                    'name': record['name'],
                    'email': record['email'],
                    'position': record['position'],
                    'created_at': str(record['created_at']) if record['created_at'] else None,
                    'department': record['department_name']
                }
                employees.append(employee)
            
            return jsonify({
                'employees': employees,
                'count': len(employees),
                'hostname': get_hostname()
            }), 200
            
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/employees', methods=['POST'])
def create_employee():
    """Create a new employee"""
    if not driver:
        return jsonify({'error': 'Database not connected'}), 500
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['name', 'email', 'position']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        with driver.session() as session:
            # Create employee
            result = session.run("""
                CREATE (e:Employee {
                    id: randomUUID(),
                    name: $name,
                    email: $email,
                    position: $position,
                    created_at: datetime()
                })
                RETURN e.id as id, e.name as name, e.email as email, 
                       e.position as position, e.created_at as created_at
            """, name=data['name'], email=data['email'], position=data['position'])
            
            employee_record = result.single()
            
            # If department is provided, link employee to department
            if 'department_id' in data:
                session.run("""
                    MATCH (e:Employee {id: $employee_id})
                    MATCH (d:Department {id: $department_id})
                    MERGE (e)-[:WORKS_IN]->(d)
                """, employee_id=employee_record['id'], department_id=data['department_id'])
            
            employee = {
                'id': employee_record['id'],
                'name': employee_record['name'],
                'email': employee_record['email'],
                'position': employee_record['position'],
                'created_at': str(employee_record['created_at'])
            }
            
            return jsonify({
                'message': 'Employee created successfully',
                'employee': employee,
                'hostname': get_hostname()
            }), 201
            
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Get a specific employee by ID"""
    if not driver:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (e:Employee {id: $id})
                OPTIONAL MATCH (e)-[:WORKS_IN]->(d:Department)
                RETURN e.id as id, e.name as name, e.email as email, 
                       e.position as position, e.created_at as created_at,
                       d.id as department_id, d.name as department_name
            """, id=employee_id)
            
            record = result.single()
            if not record:
                return jsonify({'error': 'Employee not found'}), 404
            
            employee = {
                'id': record['id'],
                'name': record['name'],
                'email': record['email'],
                'position': record['position'],
                'created_at': str(record['created_at']),
                'department': {
                    'id': record['department_id'],
                    'name': record['department_name']
                } if record['department_id'] else None
            }
            
            return jsonify({
                'employee': employee,
                'hostname': get_hostname()
            }), 200
            
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/departments', methods=['GET'])
def get_departments():
    """List all departments"""
    if not driver:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (d:Department)
                OPTIONAL MATCH (d)<-[:WORKS_IN]-(e:Employee)
                RETURN d.id as id, d.name as name, d.description as description,
                       d.created_at as created_at, count(e) as employee_count
                ORDER BY d.name
            """)
            
            departments = []
            for record in result:
                department = {
                    'id': record['id'],
                    'name': record['name'],
                    'description': record['description'],
                    'created_at': str(record['created_at']) if record['created_at'] else None,
                    'employee_count': record['employee_count']
                }
                departments.append(department)
            
            return jsonify({
                'departments': departments,
                'count': len(departments),
                'hostname': get_hostname()
            }), 200
            
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/departments', methods=['POST'])
def create_department():
    """Create a new department"""
    if not driver:
        return jsonify({'error': 'Database not connected'}), 500
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'name' not in data:
        return jsonify({'error': 'Missing required field: name'}), 400
    
    try:
        with driver.session() as session:
            result = session.run("""
                CREATE (d:Department {
                    id: randomUUID(),
                    name: $name,
                    description: $description,
                    created_at: datetime()
                })
                RETURN d.id as id, d.name as name, d.description as description,
                       d.created_at as created_at
            """, name=data['name'], description=data.get('description', ''))
            
            department_record = result.single()
            
            department = {
                'id': department_record['id'],
                'name': department_record['name'],
                'description': department_record['description'],
                'created_at': str(department_record['created_at'])
            }
            
            return jsonify({
                'message': 'Department created successfully',
                'department': department,
                'hostname': get_hostname()
            }), 201
            
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/departments/<department_id>', methods=['GET'])
def get_department(department_id):
    """Get a specific department by ID"""
    if not driver:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        with driver.session() as session:
            # Get department info
            dept_result = session.run("""
                MATCH (d:Department {id: $id})
                RETURN d.id as id, d.name as name, d.description as description,
                       d.created_at as created_at
            """, id=department_id)
            
            dept_record = dept_result.single()
            if not dept_record:
                return jsonify({'error': 'Department not found'}), 404
            
            # Get employees in this department
            emp_result = session.run("""
                MATCH (d:Department {id: $id})<-[:WORKS_IN]-(e:Employee)
                RETURN e.id as id, e.name as name, e.email as email, e.position as position
            """, id=department_id)
            
            employees = []
            for record in emp_result:
                employee = {
                    'id': record['id'],
                    'name': record['name'],
                    'email': record['email'],
                    'position': record['position']
                }
                employees.append(employee)
            
            department = {
                'id': dept_record['id'],
                'name': dept_record['name'],
                'description': dept_record['description'],
                'created_at': str(dept_record['created_at']),
                'employees': employees,
                'employee_count': len(employees)
            }
            
            return jsonify({
                'department': department,
                'hostname': get_hostname()
            }), 200
            
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found',
        'hostname': get_hostname()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An internal server error occurred',
        'hostname': get_hostname()
    }), 500

if __name__ == '__main__':
    # Initialize Neo4j connection
    init_neo4j()
    
    # Run the app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)