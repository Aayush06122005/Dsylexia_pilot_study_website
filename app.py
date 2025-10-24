from flask import Flask, request, jsonify, session, flash, redirect, url_for, render_template, send_from_directory
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import json
import bcrypt
import os
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth


# Load environment variables only in local dev (Railway will already have them set)
if not os.getenv("RAILWAY_ENVIRONMENT"):
    from dotenv import load_dotenv
    load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dyslexia_research_study_2025")
CORS(app)

DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "localhost"),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", ""),
    "database": os.getenv("MYSQLDATABASE", "aviendbnew"),
    "port": int(os.getenv("MYSQLPORT", 3306))
}

def ensure_suggested_tasks_table():
    """Create suggested_tasks table if it doesn't exist."""
    conn = connect_db()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS suggested_tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                school_id INT NOT NULL,
                task_name VARCHAR(255) NOT NULL,
                category VARCHAR(100) NOT NULL,
                description TEXT,
                estimated_time INT,
                devices_required VARCHAR(255),
                details TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_id) REFERENCES schools(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        conn.commit()
    except Exception as e:
        print(f"Error ensuring suggested_tasks table: {e}")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

def connect_db():
    """Establishes a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Connected to the database successfully!")
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Ensure suggested_tasks table exists after DB connector is defined
ensure_suggested_tasks_table()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'wav', 'webm', 'mp3', 'ogg', 'm4a', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Set up OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url=os.getenv("GOOGLE_METADATA_URL", ""),  
    # access_token_url='https://accounts.google.com/o/oauth2/token',
    # access_token_params=None,
    # authorize_url='https://accounts.google.com/o/oauth2/auth',
    # authorize_params=None,
    # api_base_url='https://www.googleapis.com/oauth2/v1/',
    # userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)
@app.route('/login/google')
def login_google():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/callback/google')
def google_callback():
    token = google.authorize_access_token()
    # user_info = google.get('userinfo').json()
    user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    session['user'] = user_info
    session['email'] = user_info['email']
    # Check if user exists, else create
    user_id = get_user_id(user_info['email'])
    if not user_id:
        # You may want to use user_info['name'] or user_info['given_name']
        create_user(user_info.get('name', ''), user_info['email'], '', True)
        user_id = get_user_id(user_info['email'])
    session['user_id'] = user_id
    # Check consent
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT consent_given FROM consent_data WHERE user_id = %s ORDER BY consent_date DESC LIMIT 1", (user_id,))
    consent = cursor.fetchone()
    cursor.close()
    conn.close()

    # Check demographics
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM demographics WHERE user_id = %s", (user_id,))
    demographics = cursor.fetchone()
    cursor.close()
    conn.close()

    if not demographics:
        return redirect(url_for('profile_setup'))

    # Get user type for dashboard redirect
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_type FROM users WHERE id = %s", (user_id,))
    user_type = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    if user_type == 'parent':
        return redirect(url_for('parent_page'))
    elif user_type == 'school':
        return redirect(url_for('school_page'))
    else:
        return redirect(url_for('participant_dashboard'))

# def connect_db():
#     """Establishes a connection to the MySQL database."""
#     try:
#         conn = mysql.connector.connect(**DB_CONFIG)
#         print("Connected to the database successfully!")
#         return conn
#     except mysql.connector.Error as err:
#         print(f"Error: {err}")
#         return None

def create_user(name, email, password_hash, is_18_or_above, user_type='participant', parent_id=None, school_id=None):
    """Inserts a new user into the users table."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        query = """
        INSERT INTO users (name, email, password_hash, is_18_or_above, user_type, parent_id, school_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (name, email, password_hash, is_18_or_above, user_type, parent_id, school_id))
            conn.commit()
            print("User created successfully!")
            return True
        except Exception as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def get_db_cursor(dictionary: bool = False):
    conn = connect_db()
    if not conn:
        return None, None
    return conn, conn.cursor(dictionary=dictionary)

def ensure_school_logged_in():
    if 'school_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in as a school'}), 401
    return None

def create_school(name, email, password_hash, address=None, phone=None):
    """Inserts a new school into the schools table."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        query = """
        INSERT INTO schools (name, email, password_hash, address, phone)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (name, email, password_hash, address, phone))
            conn.commit()
            print("School created successfully!")
            return True
        except Exception as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def get_school_id(email):
    """Fetches the school ID from the database based on the email."""
    try:
        conn = connect_db()
        if not conn:
            return None
        cursor = conn.cursor()
        query = "SELECT id FROM schools WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_school_exists(email):
    """Check if a school with the given email already exists."""
    try:
        conn = connect_db()
        if not conn:
            return False
        cursor = conn.cursor()
        query = "SELECT id FROM schools WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Error: {e}")
        return False

def get_user_id(email):
    """Fetches the user ID from the database based on the email."""
    try:
        conn = connect_db()
        if not conn:
            return None
        cursor = conn.cursor()
        query = "SELECT id FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_user_name(user_id):
    """Fetches the user's name from the database based on user_id."""
    try:
        conn = connect_db()
        if not conn:
            return None
        cursor = conn.cursor()
        query = "SELECT name FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_user_exists(email):
    """Check if a user with the given email already exists."""
    try:
        conn = connect_db()
        if not conn:
            return False
        cursor = conn.cursor()
        query = "SELECT id FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Error: {e}")
        return False
    
@app.route('/school.html')
def school_page():
    # Check if user is logged in and is a school
    if 'school_id' not in session:
        flash('Please log in to access the school dashboard', 'error')
        return redirect(url_for('signin'))
    
    # Check if user is a school
    if session.get('user_type') != 'school':
        flash('Access denied. Only schools can access this page.', 'error')
        return redirect(url_for('landing'))
    
    return render_template('school.html')

@app.route('/school-signup')
def school_signup():
    return render_template('school_signup.html')
    
@app.route('/student-signin')
def student_signin():
    return render_template('student_signin.html')

@app.route('/api/student-login', methods=['POST'])
def student_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor()
        # Username is stored in the email field for children
        query = "SELECT id, password_hash FROM users WHERE email = %s AND user_type = 'child'"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if not result:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        user_id, stored_password_hash = result
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            session['user_id'] = user_id
            session['user_type'] = 'child'
            return jsonify({'success': True, 'message': 'Login successful!'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        print(f"Student login error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

        
@app.route('/parent')
def parent_page():
    # Check if user is logged in and is a parent
    if 'user_id' not in session:
        flash('Please log in to access the parent dashboard', 'error')
        return redirect(url_for('signin'))
    
    # Check if user is a parent
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        query = "SELECT user_type FROM users WHERE id = %s"
        cursor.execute(query, (session['user_id'],))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result or result[0] != 'parent':
            flash('Access denied. Only parents can access this page.', 'error')
            return redirect(url_for('landing'))
    
    return render_template('parent.html')




def create_task_html(task_name, instructions, estimated_time, devices_required, example, main_content):
    safe_name = task_name.lower().replace(' ', '_')
    filename = os.path.join('templates', f"task_{safe_name}.html")

    # Load the base template from task11.html
    with open(os.path.join('templates', 'task11.html'), 'r', encoding='utf-8') as f:
        base_html = f.read()

    # Prepare the info popup and main content
    main_content = f"""
    <script>
        const TASK_NAME = "{task_name}";
    </script>
    <div id="task-info-popup" style="display:block;">
        <h2>{task_name}</h2>
        <p><strong>Instructions:</strong> {instructions}</p>
        <p><strong>Estimated Time:</strong> {estimated_time} minutes</p>
        <p><strong>Devices Required:</strong> {devices_required}</p>
        <p><strong>Example:</strong> {example}</p>
        <button onclick="document.getElementById('task-info-popup').style.display='none';document.getElementById('task-content').style.display='block';">I understand, proceed</button>
    </div>
    <div id="task-content" style="display:none;">
        {main_content}
    </div>
    """

    # Replace the main content placeholder in the base template
    final_html = base_html.replace('<!-- TASK_MAIN_CONTENT -->', info_popup)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_html)

    # Dynamically add a Flask route for this task page
    route_path = f"/task_{safe_name}.html"
    template_name = f"task_{safe_name}.html"

    def render_task():
        return render_template(template_name)

    # if route_path not in [rule.rule for rule in app.url_map.iter_rules()]:
    #     app.add_url_rule(route_path, f"task_{safe_name}", render_task)



@app.route('/task_<safe_name>.html')
def task_dynamic(safe_name):
    template_name = f"task_{safe_name}.html"
    # Optionally, check if the template exists
    template_path = os.path.join('templates', template_name)
    if not os.path.exists(template_path):
        return "Task page not found.", 404
    return render_template(template_name)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration form submission."""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            is_18_or_above = request.form.get('eligibility') == 'on'
            if not name or not email or not password or not is_18_or_above:
                flash('All fields are required and eligibility must be confirmed', 'error')
                return render_template('signup.html')
            if check_user_exists(email):
                flash('User with this email already exists', 'error')
                return render_template('signup.html')
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            if create_user(name, email, password_hash, is_18_or_above):
                user_id = get_user_id(email)
                if user_id:
                    session['user_id'] = user_id
                    session['email'] = email
                flash('Registration successful!', 'success')
                return redirect(url_for('consent'))
            else:
                flash('Failed to create user', 'error')
                return render_template('signup.html')
        except Exception as e:
            print(f"Registration error: {e}")
            flash('Internal server error', 'error')
            return render_template('signup.html')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login form submission."""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            if not email or not password:
                flash('Email and password are required', 'error')
                return render_template('signin.html')
            conn = connect_db()
            if not conn:
                flash('Database connection failed', 'error')
                return render_template('signin.html')
            cursor = conn.cursor()
            query = "SELECT id, password_hash FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if not result:
                flash('Invalid credentials', 'error')
                return render_template('signin.html')
            user_id, stored_password_hash = result
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                session['user_id'] = user_id
                session['email'] = email
                flash('Login successful!', 'success')
                return redirect(url_for('participant_dashboard'))
            else:
                flash('Invalid credentials', 'error')
                return render_template('signin.html')
        except Exception as e:
            print(f"Login error: {e}")
            flash('Internal server error', 'error')
            return render_template('signin.html')
    return render_template('signin.html')

@app.route('/api/consent', methods=['POST'])
def api_consent():
    """API endpoint to store consent status and timestamp, and check digital signature."""
    user_id = request.args.get('child_id') or session.get('user_id')
    # if not user_id:
    #     return jsonify({'success': False, 'message': 'User not logged in'}), 401
    print("Consent API called. user_id:", user_id)
    data = request.get_json()
    consent_given = data.get('consent_given')
    consent_date = data.get('consent_date')
    # signature = data.get('signature', '').strip()
    # Fetch user's name from DB
    # user_name = get_user_name(user_id)
    # if not user_name or signature.lower() != user_name.lower():
    #     return jsonify({'success': False, 'message': 'Digital signature must match your name (case-insensitive)'}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = "INSERT INTO consent_data (user_id, consent_given, consent_date) VALUES (%s, %s, %s)"
        cursor.execute(query, (user_id, consent_given, consent_date))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Consent recorded'})
    except Exception as e:
        print(f"Consent error: {e}")
        return jsonify({'success': False, 'message': 'Failed to record consent'}), 500

@app.route('/api/demographics', methods=['POST'])
def api_demographics():
    """API endpoint to store profile setup/demographics data."""
    # Accept child_id as query param or in JSON
    child_id = request.args.get('child_id') or request.json.get('child_id')
    user_id = child_id or session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    data = request.get_json()
    dob = data.get('dob')
    gender = data.get('gender')
    native_language = data.get('native_language')
    education_level = data.get('education_level')
    dyslexia_status = data.get('dyslexia_status')
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = """
            INSERT INTO demographics (user_id, date_of_birth, gender, native_language, education_level, dyslexia_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, dob, gender, native_language, education_level, dyslexia_status))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Demographics recorded'})
    except Exception as e:
        print(f"Demographics error: {e}")
        return jsonify({'success': False, 'message': 'Failed to record demographics'}), 500
    
@app.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint to handle user registration."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        # Extract form data
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Check if user already exists
        if check_user_exists(email):
            return jsonify({'success': False, 'message': 'User with this email already exists'}), 409
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Get parent_id from session if this is a child registration
        parent_id = session.get('parent_id') if 'parent_id' in session else None
        
        # Create user
        if create_user(data.get('name', ''), email, password_hash, True, 'child' if parent_id else 'participant', parent_id, None):
            # Get user ID for session
            user_id = get_user_id(email)
            if user_id:
                session['user_id'] = user_id
                session['email'] = email
                # Clear parent_id from session after successful registration
                if 'parent_id' in session:
                    del session['parent_id']
            
            return jsonify({
                'success': True, 
                'message': 'Registration successful!',
                'user_id': user_id
            }), 201
        else:
            return jsonify({'success': False, 'message': 'Failed to create user'}), 500
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/parent-login-child', methods=['POST'])
def parent_login_child():
    """API endpoint for parent to directly login their child."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        child_id = data.get('child_id')
        
        if not child_id:
            return jsonify({'success': False, 'message': 'Child ID is required'}), 400
        
        # Check if we have a parent session (either current or stored)
        if 'parent_user_id' in session:
            # We're switching from child back to parent, use stored parent info
            parent_id = session['parent_user_id']
        elif 'user_id' in session and 'user_type' in session and session['user_type'] == 'parent':
            # We're currently logged in as parent
            parent_id = session['user_id']
        else:
            return jsonify({'success': False, 'message': 'Parent must be logged in'}), 401
        
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Verify that this parent has access to this child
        cursor.execute("""
            SELECT pc.child_id, u.email, u.user_type 
            FROM parent_children pc 
            JOIN users u ON pc.child_id = u.id 
            WHERE pc.parent_id = %s AND pc.child_id = %s
        """, (parent_id, child_id))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'message': 'Child not found or access denied'}), 404
        
        child_id_from_db, child_email, child_user_type = result
        
        if child_user_type != 'child':
            return jsonify({'success': False, 'message': 'Invalid child account'}), 400
        
        # Store parent session info before switching to child
        session['parent_user_id'] = parent_id
        session['parent_email'] = session.get('email')
        session['parent_user_type'] = 'parent'
        
        # Log in the child
        session['user_id'] = child_id_from_db
        session['email'] = child_email
        session['user_type'] = 'child'
        
        return jsonify({
            'success': True,
            'message': 'Child logged in successfully',
            'child_id': child_id_from_db,
            'email': child_email,
            'user_type': 'child'
        })
        
    except Exception as e:
        print(f"Parent login child error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/switch-back-to-parent', methods=['POST'])
def switch_back_to_parent():
    """API endpoint to switch back from child session to parent session."""
    try:
        # Check if we have parent session stored
        if 'parent_user_id' not in session:
            return jsonify({'success': False, 'message': 'No parent session found'}), 400
        
        # Restore parent session
        session['user_id'] = session['parent_user_id']
        session['email'] = session['parent_email']
        session['user_type'] = session['parent_user_type']
        
        # Clean up parent session data
        session.pop('parent_user_id', None)
        session.pop('parent_email', None)
        session.pop('parent_user_type', None)
        
        return jsonify({
            'success': True,
            'message': 'Switched back to parent session',
            'user_id': session['user_id'],
            'email': session['email'],
            'user_type': session['user_type']
        })
        
    except Exception as e:
        print(f"Switch back to parent error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/unified-login', methods=['POST'])
def unified_login():
    """Unified API endpoint to handle login for all user types (school, parent, child)."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # First check schools table
        cursor.execute("SELECT id, password_hash FROM schools WHERE email = %s", (email,))
        school_result = cursor.fetchone()
        
        if school_result:
            school_id, stored_password_hash = school_result
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                session['school_id'] = school_id
                session['email'] = email
                session['user_type'] = 'school'
                cursor.close()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': 'School login successful!',
                    'school_id': school_id,
                    'email': email,
                    'user_type': 'school'
                })
        
        # Then check users table (parent, child, participant)
        cursor.execute("SELECT id, password_hash, user_type FROM users WHERE email = %s", (email,))
        user_result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user_result:
            user_id, stored_password_hash, user_type = user_result
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                session['user_id'] = user_id
                session['email'] = email
                session['user_type'] = user_type
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful!',
                    'user_id': user_id,
                    'email': email,
                    'user_type': user_type
                })
        
        # If no match found in either table
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"Unified login error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint to handle user login."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        # Check user credentials
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        query = "SELECT id, password_hash FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        user_id, stored_password_hash = result
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            # Get user type
            conn = connect_db()
            if conn:
                cursor = conn.cursor()
                query = "SELECT user_type FROM users WHERE id = %s"
                cursor.execute(query, (user_id,))
                user_type_result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                session['user_id'] = user_id
                session['email'] = email
                session['user_type'] = user_type_result[0] if user_type_result else 'participant'
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful!',
                    'user_id': user_id,
                    'email': email,
                    'user_type': session['user_type']
                })
            else:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """API endpoint to handle user logout."""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/parent/register', methods=['POST'])
def parent_register():
    """API endpoint to handle parent registration.
    If a parent email exists without password, set password. If none exists, create a new parent.
    Also claim any inactive children with pending_parent_email matching this parent and activate them.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400

        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500

        # Look up existing parent by email
        cur.execute("SELECT id, password_hash, school_id FROM users WHERE email=%s AND user_type='parent'", (email,))
        existing = cur.fetchone()

        if existing:
            user_id, password_hash_db, school_id = existing
            if password_hash_db is not None:
                cur.close(); conn.close()
                return jsonify({'success': False, 'message': 'You are already registered. Please sign in.'}), 409
            # set password and name
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute("UPDATE users SET name=%s, password_hash=%s WHERE id=%s", (name, password_hash, user_id))
        else:
            # Create fresh parent (not previously added by school)
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute(
                "INSERT INTO users (name, email, password_hash, is_18_or_above, user_type) VALUES (%s,%s,%s,%s,'parent')",
                (name, email, password_hash, True)
            )
            user_id = cur.lastrowid

        # Claim inactive children for this parent email
        cur.execute(
            "SELECT id FROM users WHERE user_type='child' AND is_active=FALSE AND pending_parent_email=%s",
            (email,)
        )
        children = [row[0] for row in cur.fetchall()]
        for child_id in children:
            cur.execute("UPDATE users SET is_active=TRUE, pending_parent_email=NULL, parent_id=%s WHERE id=%s", (user_id, child_id))
            try:
                cur.execute("INSERT IGNORE INTO parent_children (parent_id, child_id) VALUES (%s,%s)", (user_id, child_id))
            except Exception:
                pass

        conn.commit()
        cur.close(); conn.close()

        session['user_id'] = user_id
        session['email'] = email
        session['user_type'] = 'parent'

        return jsonify({'success': True, 'message': 'Parent registration successful!', 'user_id': user_id}), 201

    except Exception as e:
        print(f"Parent registration error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/parent/add-child', methods=['POST'])
def add_child():
    """API endpoint to add a child to a parent account."""
    try:
        # Check if user is logged in and is a parent
        if 'user_id' not in session or session.get('user_type') != 'parent':
            return jsonify({'success': False, 'message': 'Please log in as a parent'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400

        username = data.get('username', '').strip()  # This will be stored in email field
        password = data.get('password', '')
        name = data.get('name', '').strip()

        # Validation
        if not username or not password or not name:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        # Check if username (email field) already exists
        if check_user_exists(username):
            return jsonify({'success': False, 'message': 'Username already exists'}), 409

        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create child user with parent_id
        if create_user(name, username, password_hash, True, 'child', session['user_id']):
            # Get child user ID
            child_id = get_user_id(username)
            # Add to parent_children table
            conn = connect_db()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO parent_children (parent_id, child_id) VALUES (%s, %s)", 
                                 (session['user_id'], child_id))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    print(f"Error adding to parent_children: {e}")
                finally:
                    cursor.close()
                    conn.close()
            # Return child_id so frontend can redirect to consent
            return jsonify({
                'success': True, 
                'message': 'Child account created successfully!',
                'child_id': child_id
            }), 201
        else:
            return jsonify({'success': False, 'message': 'Failed to create child account'}), 500

    except Exception as e:
        print(f"Add child error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/parent/children', methods=['GET'])
def get_parent_children():
    """API endpoint to get all children of a parent."""
    try:
        # Check if user is logged in and is a parent
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please log in as a parent'}), 401
        
        conn = connect_db()
        if conn:
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT u.id, u.name, u.email, u.created_at, u.user_type
            FROM users u
            WHERE u.parent_id = %s AND u.user_type = 'child'
            ORDER BY u.created_at DESC
            """
            cursor.execute(query, (session['user_id'],))
            children = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'children': children})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Get children error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# --- Parent: Child Details API ---
@app.route('/api/parent/child-details', methods=['GET'])
def get_parent_child_details():
    """Return detailed info for a specific child belonging to the logged-in parent, including school/class/section.
       For non-school children, return NA for school, class, section.
    """
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please log in as a parent'}), 401
        child_id = request.args.get('child_id', type=int)
        if not child_id:
            return jsonify({'success': False, 'message': 'child_id is required'}), 400

        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        cursor = conn.cursor(dictionary=True)
        try:
            # Ensure the child belongs to this parent (direct parent_id or via parent_children table)
            cursor.execute(
                """
                SELECT u.id FROM users u
                WHERE u.id = %s AND u.user_type = 'child' AND (
                    u.parent_id = %s OR EXISTS (
                        SELECT 1 FROM parent_children pc WHERE pc.child_id = u.id AND pc.parent_id = %s
                    )
                )
                """,
                (child_id, session['user_id'], session['user_id'])
            )
            if not cursor.fetchone():
                cursor.close(); conn.close()
                return jsonify({'success': False, 'message': 'Child not found'}), 404

            # Fetch child details with joins to section, class, school
            cursor.execute(
                """
                SELECT 
                    u.id, u.name, u.email, u.created_at,
                    u.school_id,
                    scls.name AS school_name,
                    sec.id AS section_id,
                    sec.name AS section_name,
                    cls.id AS class_id,
                    cls.name AS class_name,
                    d.age, d.gender, d.dyslexia_status, d.education_level, d.native_language
                FROM users u
                LEFT JOIN class_sections sec ON sec.id = u.section_id
                LEFT JOIN school_classes cls ON cls.id = sec.class_id
                LEFT JOIN schools scls ON scls.id = u.school_id
                LEFT JOIN demographics d ON d.user_id = u.id
                WHERE u.id = %s
                """,
                (child_id,)
            )
            row = cursor.fetchone()
            if not row:
                cursor.close(); conn.close()
                return jsonify({'success': False, 'message': 'Child not found'}), 404

            # Normalize NA values
            if not row.get('school_id'):
                row['school_name'] = 'NA'
                row['class_name'] = 'NA'
                row['section_name'] = 'NA'
            result = {
                'id': row['id'],
                'name': row['name'],
                'email': row.get('email'),
                'created_at': row.get('created_at'),
                'school_name': row.get('school_name') or 'NA',
                'class_name': row.get('class_name') or 'NA',
                'section_name': row.get('section_name') or 'NA',
                'age': row.get('age'),
                'gender': row.get('gender'),
                'dyslexia_status': row.get('dyslexia_status'),
                'education_level': row.get('education_level'),
                'native_language': row.get('native_language')
            }
            cursor.close(); conn.close()
            return jsonify({'success': True, 'child': result})
        except Exception as ie:
            cursor.close(); conn.close()
            print(f"Parent child details error: {ie}")
            return jsonify({'success': False, 'message': 'Failed to fetch child details'}), 500
    except Exception as e:
        print(f"Parent child details outer error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/register', methods=['POST'])
def school_register():
    """API endpoint to handle school registration."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        # Extract form data
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        address = data.get('address', '').strip()
        phone = data.get('phone', '').strip()
        
        # Validation
        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'Name, email, and password are required'}), 400
        
        # Check if school already exists
        if check_school_exists(email):
            return jsonify({'success': False, 'message': 'School with this email already exists'}), 409
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create school
        if create_school(name, email, password_hash, address, phone):
            # Get school ID for session
            school_id = get_school_id(email)
            if school_id:
                session['school_id'] = school_id
                session['email'] = email
                session['user_type'] = 'school'
            
            return jsonify({
                'success': True, 
                'message': 'School registration successful!',
                'school_id': school_id
            }), 201
        else:
            return jsonify({'success': False, 'message': 'Failed to create school account'}), 500
            
    except Exception as e:
        print(f"School registration error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/login', methods=['POST'])
def school_login():
    """API endpoint to handle school login."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        # Check school credentials
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        query = "SELECT id, password_hash FROM schools WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        school_id, stored_password_hash = result
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            session['school_id'] = school_id
            session['email'] = email
            session['user_type'] = 'school'
            
            return jsonify({
                'success': True,
                'message': 'School login successful!',
                'school_id': school_id,
                'email': email,
                'user_type': 'school'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"School login error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/add-parent', methods=['POST'])
def add_parent():
    """API endpoint to add a parent to a school account."""
    try:
        # Check if user is logged in and is a school
        if 'school_id' not in session:
            return jsonify({'success': False, 'message': 'Please log in as a school'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        # Extract form data
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        
        # Validation
        if not name or not email:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Check if user already exists
        if check_user_exists(email):
            return jsonify({'success': False, 'message': 'User with this email already exists'}), 409
         
        # Create parent user with school_id
        if create_user(name, email, None, True, 'parent', None, session['school_id']):
            # Get parent user ID
            parent_id = get_user_id(email)
            
            # Add to school_parents table
            conn = connect_db()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO school_parents (school_id, parent_id) VALUES (%s, %s)", 
                                 (session['school_id'], parent_id))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    print(f"Error adding to school_parents: {e}")
                finally:
                    cursor.close()
                    conn.close()
            
            return jsonify({
                'success': True, 
                'message': 'Parent account created successfully!',
                'parent_id': parent_id
            }), 201
        else:
            return jsonify({'success': False, 'message': 'Failed to create parent account'}), 500
            
    except Exception as e:
        print(f"Add parent error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/class-stats')
def get_class_stats():
    """Get class-wise statistics for the current school."""
    if 'school_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # Get stats grouped by class, counting parents and their children
        cursor.execute('''
            SELECT 
                u1.class,
                COUNT(DISTINCT CASE WHEN u1.user_type = 'parent' THEN u1.id END) as parents,
                COUNT(DISTINCT CASE WHEN u2.user_type = 'child' THEN u2.id END) as students
            FROM users u1
            LEFT JOIN parent_children pc ON u1.id = pc.parent_id
            LEFT JOIN users u2 ON pc.child_id = u2.id
            WHERE u1.school_id = %s AND u1.class IS NOT NULL
            GROUP BY u1.class
            ORDER BY u1.class
        ''', (session['school_id'],))

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format the stats
        stats = {}
        for row in results:
            if row['class']:
                stats[row['class']] = {
                    'parents': int(row['parents'] or 0),
                    'students': int(row['students'] or 0)
                }

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        print(f"Error getting class stats: {e}")
        return jsonify({'success': False, 'message': 'Failed to load statistics'}), 500

@app.route('/api/school/parents', methods=['GET'])
def get_school_parents():
    """API endpoint to get all parents of a school."""
    try:
        # Check if user is logged in and is a school
        if 'school_id' not in session:
            print(f"Session data: {dict(session)}")
            return jsonify({'success': False, 'message': 'Please log in as a school'}), 401
        
        print(f"School ID from session: {session['school_id']}")
        
        conn = connect_db()
        if conn:
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT u.id, u.name, u.email, u.created_at, u.user_type
            FROM users u
            WHERE u.school_id = %s AND u.user_type = 'parent'
            ORDER BY u.created_at DESC
            """
            cursor.execute(query, (session['school_id'],))
            parents = cursor.fetchall()
            cursor.close()
            conn.close()
            
            print(f"Found {len(parents)} parents for school {session['school_id']}")
            
            return jsonify({
                'success': True,
                'parents': parents
            })
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Get parents error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ---------- Classes & Sections APIs ----------

@app.route('/api/school/classes', methods=['GET'])
def list_classes():
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        cur.execute("""
            SELECT c.id, c.name, c.academic_year,
                   COUNT(DISTINCT s.id) AS sections
            FROM school_classes c
            LEFT JOIN class_sections s ON s.class_id = c.id
            WHERE c.school_id = %s
            GROUP BY c.id
            ORDER BY c.academic_year DESC, c.name ASC
        """, (session['school_id'],))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({'success': True, 'classes': rows})
    except Exception as e:
        print(f"List classes error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/classes', methods=['POST'])
def create_class():
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        academic_year = data.get('academic_year')
        if not name:
            return jsonify({'success': False, 'message': 'Class name is required'}), 400
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        try:
            cur.execute(
                """
                INSERT INTO school_classes (school_id, name, academic_year)
                VALUES (%s, %s, %s)
                """,
                (session['school_id'], name, academic_year)
            )
            conn.commit()
            new_id = cur.lastrowid
            return jsonify({'success': True, 'id': new_id})
        except Exception as e:
            conn.rollback(); print(f"Create class error: {e}")
            return jsonify({'success': False, 'message': 'Failed to create class'}), 500
        finally:
            cur.close(); conn.close()
    except Exception as e:
        print(f"Create class outer error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/classes/<int:class_id>/sections', methods=['GET'])
def list_sections(class_id: int):
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        # Verify class belongs to school
        cur.execute("SELECT id FROM school_classes WHERE id=%s AND school_id=%s", (class_id, session['school_id']))
        if not cur.fetchone():
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'Not found'}), 404
        cur.execute("""
            SELECT id, name FROM class_sections WHERE class_id=%s ORDER BY name ASC
        """, (class_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({'success': True, 'sections': rows})
    except Exception as e:
        print(f"List sections error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/classes/<int:class_id>/sections', methods=['POST'])
def create_section(class_id: int):
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'success': False, 'message': 'Section name is required'}), 400
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        try:
            # Verify class belongs to school
            cur.execute("SELECT id FROM school_classes WHERE id=%s AND school_id=%s", (class_id, session['school_id']))
            if not cur.fetchone():
                return jsonify({'success': False, 'message': 'Not found'}), 404
            cur.execute(
                "INSERT INTO class_sections (class_id, name) VALUES (%s, %s)",
                (class_id, name)
            )
            conn.commit()
            return jsonify({'success': True, 'id': cur.lastrowid})
        except Exception as e:
            conn.rollback(); print(f"Create section error: {e}")
            return jsonify({'success': False, 'message': 'Failed to create section'}), 500
        finally:
            cur.close(); conn.close()
    except Exception as e:
        print(f"Create section outer error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ---------- Students management ----------

@app.route('/api/school/sections/<int:section_id>/students', methods=['POST'])
def add_student_to_section(section_id: int):
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        data = request.get_json() or {}
        student_name = (data.get('student_name') or '').strip()
        parent_email = (data.get('parent_email') or '').strip().lower()
        student_email = (data.get('student_email') or '').strip().lower() or None
        if not student_name or not parent_email:
            return jsonify({'success': False, 'message': 'student_name and parent_email are required'}), 400
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        try:
            # Verify section belongs to school
            cur.execute(
                """
                SELECT s.id FROM class_sections s
                JOIN school_classes c ON c.id = s.class_id
                WHERE s.id=%s AND c.school_id=%s
                """,
                (section_id, session['school_id'])
            )
            if not cur.fetchone():
                return jsonify({'success': False, 'message': 'Not found'}), 404

            # Ensure parent user exists or create placeholder inactive parent under this school
            cur.execute("SELECT id FROM users WHERE email=%s AND user_type='parent'", (parent_email,))
            parent_user = cur.fetchone()
            parent_id = None
            if parent_user:
                parent_id = parent_user[0]
                # Also associate parent to the school's section for convenience
                try:
                    cur.execute("UPDATE users SET school_id=%s, section_id=%s WHERE id=%s AND user_type='parent'", (session['school_id'], section_id, parent_id))
                except Exception:
                    pass
            else:
                cur.execute(
                    "INSERT INTO users (name, email, password_hash, is_18_or_above, user_type, school_id, section_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (parent_email.split('@')[0].title(), parent_email, None, True, 'parent', session['school_id'], section_id)
                )
                parent_id = cur.lastrowid

            # Create inactive child linked to pending parent email and section
            cur.execute(
                """
                INSERT INTO users (name, email, password_hash, is_18_or_above, user_type, parent_id, school_id, section_id, is_active, pending_parent_email)
                VALUES (%s, %s, %s, %s, 'child', %s, %s, %s, %s, %s)
                """,
                (student_name, student_email, None, True, parent_id, session['school_id'], section_id, False, parent_email)
            )
            child_id = cur.lastrowid

            # Link in parent_children if parent exists
            if parent_id:
                try:
                    cur.execute("INSERT IGNORE INTO parent_children (parent_id, child_id) VALUES (%s,%s)", (parent_id, child_id))
                except Exception:
                    pass

            conn.commit()
            return jsonify({'success': True, 'child_id': child_id})
        except Exception as e:
            conn.rollback(); print(f"Add student error: {e}")
            return jsonify({'success': False, 'message': 'Failed to add student'}), 500
        finally:
            cur.close(); conn.close()
    except Exception as e:
        print(f"Add student outer error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/sections/<int:section_id>/students/bulk', methods=['POST'])
def bulk_add_students(section_id: int):
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        data = request.get_json() or {}
        rows = data.get('students') or []
        if not isinstance(rows, list):
            return jsonify({'success': False, 'message': 'students must be a list'}), 400
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        added = 0; failed = 0
        try:
            # Verify section belongs to school
            cur.execute(
                """
                SELECT s.id FROM class_sections s
                JOIN school_classes c ON c.id = s.class_id
                WHERE s.id=%s AND c.school_id=%s
                """,
                (section_id, session['school_id'])
            )
            if not cur.fetchone():
                return jsonify({'success': False, 'message': 'Not found'}), 404
            for row in rows:
                try:
                    student_name = (row.get('student_name') or row.get('name') or '').strip()
                    parent_email = (row.get('parent_email') or row.get('Parent Email') or '').strip().lower()
                    student_email = (row.get('student_email') or row.get('Email') or '').strip().lower() or None
                    if not student_name or not parent_email:
                        failed += 1; continue
                    # ensure parent
                    cur.execute("SELECT id FROM users WHERE email=%s AND user_type='parent'", (parent_email,))
                    res = cur.fetchone()
                    if res:
                        parent_id = res[0]
                        try:
                            cur.execute("UPDATE users SET school_id=%s, section_id=%s WHERE id=%s AND user_type='parent'", (session['school_id'], section_id, parent_id))
                        except Exception:
                            pass
                    else:
                        cur.execute(
                            "INSERT INTO users (name, email, password_hash, is_18_or_above, user_type, school_id, section_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                            (parent_email.split('@')[0].title(), parent_email, None, True, 'parent', session['school_id'], section_id)
                        )
                        parent_id = cur.lastrowid
                    # child
                    cur.execute(
                        """
                        INSERT INTO users (name, email, password_hash, is_18_or_above, user_type, parent_id, school_id, section_id, is_active, pending_parent_email)
                        VALUES (%s,%s,%s,%s,'child',%s,%s,%s,%s,%s)
                        """,
                        (student_name, student_email, None, True, parent_id, session['school_id'], section_id, False, parent_email)
                    )
                    child_id = cur.lastrowid
                    try:
                        cur.execute("INSERT IGNORE INTO parent_children (parent_id, child_id) VALUES (%s,%s)", (parent_id, child_id))
                    except Exception:
                        pass
                    added += 1
                except Exception as ie:
                    print(f"Row failed: {ie}"); failed += 1
            conn.commit()
            return jsonify({'success': True, 'added': added, 'failed': failed})
        except Exception as e:
            conn.rollback(); print(f"Bulk add error: {e}")
            return jsonify({'success': False, 'message': 'Failed to bulk add'}), 500
        finally:
            cur.close(); conn.close()
    except Exception as e:
        print(f"Bulk add outer error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ---------- Section Assessments ----------

@app.route('/api/school/sections/<int:section_id>/assessments', methods=['POST'])
def assign_assessments(section_id: int):
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        data = request.get_json() or {}
        task_names = data.get('task_names') or []
        if not isinstance(task_names, list) or not task_names:
            return jsonify({'success': False, 'message': 'task_names list is required'}), 400
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        try:
            # Verify section belongs to school
            cur.execute(
                """
                SELECT s.id FROM class_sections s
                JOIN school_classes c ON c.id = s.class_id
                WHERE s.id=%s AND c.school_id=%s
                """,
                (section_id, session['school_id'])
            )
            if not cur.fetchone():
                return jsonify({'success': False, 'message': 'Not found'}), 404
            # Insert assignments
            for tname in task_names:
                cur.execute(
                    "INSERT IGNORE INTO section_assessments (section_id, task_name) VALUES (%s,%s)",
                    (section_id, tname)
                )
            conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            conn.rollback(); print(f"Assign assessments error: {e}")
            return jsonify({'success': False, 'message': 'Failed to assign assessments'}), 500
        finally:
            cur.close(); conn.close()
    except Exception as e:
        print(f"Assign assessments outer error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/class-stats', methods=['GET'])
def class_stats():
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        cur.execute(
            """
            SELECT sc.name AS class_name,
                   COUNT(CASE WHEN u.user_type='parent' THEN 1 END) AS parents,
                   COUNT(CASE WHEN u.user_type='child' THEN 1 END) AS students
            FROM users u
            LEFT JOIN school_classes sc ON sc.id = (
                SELECT c2.id FROM class_sections s2 JOIN school_classes c2 ON c2.id = s2.class_id WHERE s2.id = u.section_id LIMIT 1
            )
            WHERE u.school_id = %s
            GROUP BY sc.name
            ORDER BY sc.name
            """,
            (session['school_id'],)
        )
        rows = cur.fetchall()
        cur.close(); conn.close()
        stats = { (r['class_name'] or 'Unassigned'): {'parents': int(r['parents']), 'students': int(r['students'])} for r in rows }
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        print(f"Class stats error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ---------- Auxiliary listing endpoints ----------

@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        cur.execute("SELECT task_name, description, estimated_time FROM tasks ORDER BY task_name ASC")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({'success': True, 'tasks': rows})
    except Exception as e:
        print(f"List tasks error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/sections/<int:section_id>/students', methods=['GET'])
def list_students_in_section(section_id: int):
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        # Verify section belongs to school
        cur.execute(
            """
            SELECT s.id FROM class_sections s
            JOIN school_classes c ON c.id = s.class_id
            WHERE s.id=%s AND c.school_id=%s
            """,
            (section_id, session['school_id'])
        )
        if not cur.fetchone():
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'Not found'}), 404
        cur.execute(
            "SELECT id, name, email, is_active, created_at FROM users WHERE user_type='child' AND section_id=%s ORDER BY created_at DESC",
            (section_id,)
        )
        students = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        print(f"List students error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/sections/<int:section_id>/assessments', methods=['GET'])
def list_assigned_assessments(section_id: int):
    auth = ensure_school_logged_in()
    if auth:
        return auth
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        # Verify section belongs to school
        cur.execute(
            """
            SELECT s.id FROM class_sections s
            JOIN school_classes c ON c.id = s.class_id
            WHERE s.id=%s AND c.school_id=%s
            """,
            (section_id, session['school_id'])
        )
        if not cur.fetchone():
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'Not found'}), 404
        cur.execute("SELECT task_name, assigned_at FROM section_assessments WHERE section_id=%s ORDER BY task_name", (section_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({'success': True, 'assessments': rows})
    except Exception as e:
        print(f"List section assessments error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/school/suggest-task', methods=['POST'])
def school_suggest_task():
    """Allow logged-in schools to suggest a new task."""
    try:
        if 'school_id' not in session:
            return jsonify({'success': False, 'message': 'Please log in as a school'}), 401

        data = request.get_json() or {}
        task_name = (data.get('task_name') or '').strip()
        category = (data.get('category') or '').strip()
        description = (data.get('description') or '').strip()
        estimated_time = data.get('estimated_time')
        devices_required = (data.get('devices_required') or '').strip()
        details = (data.get('details') or '').strip()

        if not task_name or not category:
            return jsonify({'success': False, 'message': 'Task name and category are required'}), 400

        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO suggested_tasks (school_id, task_name, category, description, estimated_time, devices_required, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (session['school_id'], task_name, category, description or None, estimated_time, devices_required or None, details or None)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Task suggestion submitted'})
        except Exception as e:
            conn.rollback()
            print(f"Error inserting suggested task: {e}")
            return jsonify({'success': False, 'message': 'Failed to submit suggestion'}), 500
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Suggest task error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/user-info', methods=['GET'])
def get_user_info():
    """API endpoint to get current user information."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, email, date_of_birth, gender FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            # Convert date to string format
            if user['date_of_birth']:
                user['date_of_birth'] = user['date_of_birth'].strftime('%Y-%m-%d')
            
            return jsonify({'success': True, 'user': user})
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        print(f"Get user info error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/test-db')
def test_db():
    """Test database connection."""
    try:
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Database connection successful!'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

@app.route('/test-tasks')
def test_tasks():
    """Test tasks table."""
    try:
        conn = connect_db()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tasks")
            tasks = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': f'Found {len(tasks)} tasks', 'tasks': tasks})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

@app.route('/test-session')
def test_session():
    """Test session data."""
    session_data = {
        'user_id': session.get('user_id'),
        'school_id': session.get('school_id'),
        'email': session.get('email'),
        'user_type': session.get('user_type')
    }
    return jsonify(session_data)

# Serve HTML pages
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/signup')
def signup():
    # Check if this is a child signup from parent dashboard
    parent_id = request.args.get('parent_id')
    if parent_id:
        # Verify parent exists and is logged in
        if 'user_id' not in session or str(session['user_id']) != str(parent_id):
            flash('Access denied. Please log in as the parent.', 'error')
            return redirect(url_for('signin'))
        
        # Store parent_id in session for child registration
        session['parent_id'] = int(parent_id)
    
    return render_template('signup.html')

@app.route('/parent-signup')
def parent_signup():
    return render_template('parent_signup.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/consent')
def consent():
    return render_template('consent.html')

@app.route('/profile-setup')
def profile_setup():
    return render_template('profile-setup.html')



@app.route('/participant-dashboard')
def participant_dashboard():
    user_id = session.get('user_id')
    user_name = None
    tasks = []
    total_tasks = 0
    progress = 0
    if user_id:
        user_name = get_user_name(user_id)
        try:
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            
            # Define the core tasks for progress calculation
            core_tasks = [
                'Reading Aloud Task 1',
                'Typing Task', 
                'Reading Comprehension',
                'Mathematical Comprehension',
                'Writing Task',
                'Aptitude Test'
            ]
            
            # Determine allowed tasks based on class level from demographics
            # Get user's class level from demographics
            class_level = _get_user_class_level(conn, user_id)
            
            if class_level:
                # Show class-appropriate tasks based on class level
                # Get tasks that have class-specific content for this user's class
                db_tasks = []
                
                # Check each task category for class-appropriate content
                task_categories = [
                    ('Reading Aloud Task 1', 'reading_tasks'),
                    ('Typing Task', 'typing_tasks'), 
                    ('Reading Comprehension', 'reading_comprehension_tasks'),
                    ('Mathematical Comprehension', 'mathematical_comprehension_tasks'),
                    ('Writing Task', 'writing_tasks'),
                    ('Aptitude Test', 'aptitude_tasks')
                ]
                
                for task_name, table_name in task_categories:
                    # Check if there are class-appropriate tasks for this category
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name} WHERE class_level = %s", (class_level,))
                    count_result = cursor.fetchone()
                    if count_result and count_result['count'] > 0:
                        db_tasks.append(task_name)
                
                # If no class-specific tasks found, show all core tasks as fallback
                if not db_tasks:
                    db_tasks = core_tasks
            else:
                # No class level found: show all tasks as fallback
                cursor.execute("SELECT task_name FROM tasks")
                db_tasks = [row['task_name'] for row in cursor.fetchall()]
            
            # Get user task statuses
            cursor.execute("SELECT task_name, status FROM user_tasks WHERE user_id = %s", (user_id,))
            user_task_statuses = {t['task_name']: t['status'] for t in cursor.fetchall()}
            
            # Create task list with statuses
            for task_name in db_tasks:
                status = user_task_statuses.get(task_name, 'Not Started')
                tasks.append({'task_name': task_name, 'status': status})
            
            # Calculate progress based on core tasks only
            core_task_statuses = []
            for core_task in core_tasks:
                status = user_task_statuses.get(core_task, 'Not Started')
                core_task_statuses.append(status)
            
            total_tasks = len(core_tasks)
            completed = sum(1 for status in core_task_statuses if status == 'Completed')
            progress = int((completed / total_tasks) * 100) if total_tasks > 0 else 0
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Dashboard fetch tasks error: {e}")
    return render_template('participant-dashboard.html', user_name=user_name, tasks=tasks, progress=progress, total_tasks=total_tasks)



@app.route('/learn_more')
def learn_more():
    return render_template('learn_more.html')

@app.route('/extra')
def extra():
    return render_template('extra.html')

@app.route('/extra2')
def extra2():
    return render_template('extra2.html')

@app.route('/admin')
def admin_portal():
    if not session.get('is_admin'):
        flash('Please log in as admin to access this page', 'error')
        return redirect(url_for('admin_login'))
    return render_template('admin.html')

# --- Admin task categories pages ---
@app.route('/admin/tasks/category/<string:category_slug>')
def admin_tasks_by_category(category_slug: str):
    if not session.get('is_admin'):
        flash('Please log in as admin to access this page', 'error')
        return redirect(url_for('admin_login'))

    category_map = {
        'reading-aloud': {
            'title': 'Reading Aloud',
            'table': 'reading_tasks'
        },
        'typing': {
            'title': 'Typing Task',
            'table': 'typing_tasks'
        },
        'writing': {
            'title': 'Writing Task',
            'table': 'writing_tasks'
        },
        'reading-comprehension': {
            'title': 'Reading Comprehension',
            'table': 'reading_comprehension_tasks'
        },
        'mathematical-comprehension': {
            'title': 'Mathematical Comprehension',
            'table': 'mathematical_comprehension_tasks'
        },
        'aptitude': {
            'title': 'Aptitude Test',
            'table': 'aptitude_tasks'
        }
    }

    cfg = category_map.get(category_slug)
    if not cfg:
        flash('Unknown task category', 'error')
        return redirect(url_for('admin_portal'))

    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # Build base query per category
        base_table = cfg['table']

        cursor.execute(f"""
            SELECT *
            FROM {base_table}
            ORDER BY class_level, id
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Group by class level
        groups = {}
        for row in rows:
            class_level = row.get('class_level')
            key = class_level
            if key not in groups:
                label = f"Class {class_level}"
                groups[key] = {
                    'label': label,
                    'class_level': class_level,
                    'tasks': []
                }
            # Common fields
            task_common = {
                'id': row.get('id'),
                'task_name': row.get('task_name'),
                'difficulty_level': row.get('difficulty_level') or '-',
                'estimated_time': row.get('estimated_time') or '-',
            }
            # Add category-specific content fields for display
            if category_slug == 'reading-aloud':
                task_common['content'] = row.get('content')
                task_common['instructions'] = row.get('instructions')
            elif category_slug == 'typing':
                task_common['prompt'] = row.get('prompt')
                task_common['instructions'] = row.get('instructions')
            elif category_slug == 'writing':
                task_common['prompt'] = row.get('prompt')
                task_common['instructions'] = row.get('instructions')
            elif category_slug == 'reading-comprehension':
                task_common['passage'] = row.get('passage')
                task_common['question1'] = row.get('question1')
                task_common['question2'] = row.get('question2')
                task_common['question3'] = row.get('question3')
                # Parse JSON options if needed
                import json as _json
                a1 = row.get('answer1_options')
                a2 = row.get('answer2_options')
                try:
                    if isinstance(a1, str):
                        a1 = _json.loads(a1)
                except Exception:
                    pass
                try:
                    if isinstance(a2, str):
                        a2 = _json.loads(a2)
                except Exception:
                    pass
                task_common['answer1_options'] = a1
                task_common['answer2_options'] = a2
                task_common['answer3_type'] = row.get('answer3_type')
                task_common['instructions'] = row.get('instructions')
            elif category_slug == 'mathematical-comprehension':
                task_common['problem_text'] = row.get('problem_text')
                task_common['question1'] = row.get('question1')
                task_common['question2'] = row.get('question2')
                task_common['question3'] = row.get('question3')
                import json as _json
                a1 = row.get('answer1_options')
                a2 = row.get('answer2_options')
                try:
                    if isinstance(a1, str):
                        a1 = _json.loads(a1)
                except Exception:
                    pass
                try:
                    if isinstance(a2, str):
                        a2 = _json.loads(a2)
                except Exception:
                    pass
                task_common['answer1_options'] = a1
                task_common['answer2_options'] = a2
                task_common['answer3_type'] = row.get('answer3_type')
                task_common['instructions'] = row.get('instructions')
            elif category_slug == 'aptitude':
                import json as _json
                task_common['instructions'] = row.get('instructions')
                task_common['estimated_time'] = row.get('estimated_time')
                # Do not expose example in admin list view
                # Two possible schemas: per-question columns OR JSON arrays per section
                if 'logical_question1' in row:
                    # No example/content exposure for aptitude
                    task_common['logical_question1'] = row.get('logical_question1')
                    task_common['logical_question2'] = row.get('logical_question2')
                    task_common['numerical_question1'] = row.get('numerical_question1')
                    task_common['numerical_question2'] = row.get('numerical_question2')
                    task_common['verbal_question1'] = row.get('verbal_question1')
                    task_common['verbal_question2'] = row.get('verbal_question2')
                    task_common['spatial_question1'] = row.get('spatial_question1')
                    task_common['spatial_question2'] = row.get('spatial_question2')
                    for field in [
                        'logical_question1_options','logical_question2_options',
                        'numerical_question1_options','numerical_question2_options',
                        'verbal_question1_options','verbal_question2_options',
                        'spatial_question1_options','spatial_question2_options'
                    ]:
                        options = row.get(field)
                        try:
                            if isinstance(options, str):
                                options = _json.loads(options)
                        except Exception:
                            options = []
                        task_common[field] = options
                else:
                    # JSON-based schema
                    def parse_section(json_text):
                        try:
                            if isinstance(json_text, str):
                                return _json.loads(json_text) or []
                            return json_text or []
                        except Exception:
                            return []
                    lr = parse_section(row.get('logical_reasoning_questions'))
                    na = parse_section(row.get('numerical_ability_questions'))
                    va = parse_section(row.get('verbal_ability_questions'))
                    sr = parse_section(row.get('spatial_reasoning_questions'))
                    def set_pair(prefix, arr):
                        q1 = arr[0] if len(arr) > 0 else {}
                        q2 = arr[1] if len(arr) > 1 else {}
                        task_common[f'{prefix}_question1'] = q1.get('question')
                        task_common[f'{prefix}_question2'] = q2.get('question')
                        task_common[f'{prefix}_question1_options'] = q1.get('options') or []
                        task_common[f'{prefix}_question2_options'] = q2.get('options') or []
                    set_pair('logical', lr)
                    set_pair('numerical', na)
                    set_pair('verbal', va)
                    set_pair('spatial', sr)
            groups[key]['tasks'].append(task_common)

        # Sort groups by class_level
        age_groups = [groups[k] for k in sorted(groups.keys())]

        return render_template(
            'admin_tasks_category.html',
            category_title=cfg['title'],
            category_slug=category_slug,
            age_groups=age_groups
        )
    except Exception as e:
        print(f"Admin tasks by category error: {e}")
        flash('Failed to load tasks for this category', 'error')
        return redirect(url_for('admin_portal'))


# --- Admin category CRUD APIs ---
def _category_config(category_slug: str):
    return {
        'reading-aloud': {'table': 'reading_tasks'},
        'typing': {'table': 'typing_tasks'},
        'writing': {'table': 'writing_tasks'},
        'reading-comprehension': {'table': 'reading_comprehension_tasks'},
        'mathematical-comprehension': {'table': 'mathematical_comprehension_tasks'},
        'aptitude': {'table': 'aptitude_tasks'}
    }.get(category_slug)


def _get_user_class_level(conn, user_id: int):
    """Determine numeric class_level (1-12) for a user based on demographics.education_level, users.class, or their section's class name."""
    try:
        cur = conn.cursor(dictionary=True)
        class_level = None
        
        # First try demographics.education_level (stores class numbers 1-12)
        cur.execute("SELECT education_level FROM demographics WHERE user_id=%s", (user_id,))
        demo_row = cur.fetchone()
        if demo_row and demo_row.get('education_level'):
            try:
                class_level = int(demo_row['education_level'])
                if 1 <= class_level <= 12:
                    cur.close()
                    return class_level
            except (ValueError, TypeError):
                pass
        
        # Fallback to users.class (e.g., "Class 6" or "6")
        cur.execute("SELECT class, section_id FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        if row:
            user_class = row.get('class')
            if user_class:
                import re
                m = re.search(r"(\d+)", str(user_class))
                if m:
                    num = int(m.group(1))
                    if 1 <= num <= 12:
                        class_level = num
            if class_level is None and row.get('section_id'):
                # Derive via section -> school_classes.name (e.g., "Class 5")
                cur2 = conn.cursor(dictionary=True)
                cur2.execute(
                    """
                    SELECT sc.name AS class_name
                    FROM class_sections s
                    JOIN school_classes sc ON sc.id = s.class_id
                    WHERE s.id = %s
                    """,
                    (row['section_id'],)
                )
                r2 = cur2.fetchone()
                cur2.close()
                if r2 and r2.get('class_name'):
                    import re as _re
                    m2 = _re.search(r"(\d+)", str(r2['class_name']))
                    if m2:
                        num2 = int(m2.group(1))
                        if 1 <= num2 <= 12:
                            class_level = num2
        cur.close()
        return class_level
    except Exception:
        try:
            cur.close()
        except Exception:
            pass
        return None


@app.route('/api/admin/categories/<string:category_slug>/tasks', methods=['GET', 'POST'])
def admin_category_tasks(category_slug: str):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    cfg = _category_config(category_slug)
    if not cfg:
        return jsonify({'success': False, 'message': 'Unknown category'}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        table = cfg['table']
        if request.method == 'GET':
            cursor.execute(f"SELECT * FROM {table}")
            return jsonify({'success': True, 'tasks': cursor.fetchall()})
        else:
            data = request.get_json() or {}
            if category_slug == 'reading-aloud':
                cursor.execute(
                    """
                    INSERT INTO reading_tasks (task_name, class_level, difficulty_level, content, instructions, estimated_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data.get('task_name'), data.get('class_level'), data.get('difficulty_level'),
                        data.get('content'), data.get('instructions'), data.get('estimated_time')
                    )
                )
            elif category_slug == 'typing':
                cursor.execute(
                    """
                    INSERT INTO typing_tasks (task_name, class_level, difficulty_level, prompt, instructions, word_limit_min, word_limit_max, estimated_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data.get('task_name'), data.get('class_level'), data.get('difficulty_level'),
                        data.get('prompt'), data.get('instructions'), data.get('word_limit_min'), data.get('word_limit_max'), data.get('estimated_time')
                    )
                )
            elif category_slug == 'writing':
                cursor.execute(
                    """
                    INSERT INTO writing_tasks (task_name, class_level, difficulty_level, prompt, instructions, word_limit_min, word_limit_max, estimated_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data.get('task_name'), data.get('class_level'), data.get('difficulty_level'),
                        data.get('prompt'), data.get('instructions'), data.get('word_limit_min'), data.get('word_limit_max'), data.get('estimated_time')
                    )
                )
            elif category_slug == 'reading-comprehension':
                import json as _json
                cursor.execute(
                    """
                    INSERT INTO reading_comprehension_tasks (task_name, class_level, difficulty_level, passage, question1, question2, question3, answer1_options, answer2_options, answer3_type, instructions, estimated_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data.get('task_name'), data.get('class_level'), data.get('difficulty_level'),
                        data.get('passage'), data.get('question1'), data.get('question2'), data.get('question3'),
                        _json.dumps(data.get('answer1_options') or []), _json.dumps(data.get('answer2_options') or []),
                        data.get('answer3_type'), data.get('instructions'), data.get('estimated_time')
                    )
                )
            elif category_slug == 'mathematical-comprehension':
                import json as _json
                cursor.execute(
                    """
                    INSERT INTO mathematical_comprehension_tasks (task_name, class_level, difficulty_level, problem_text, question1, question2, question3, answer1_options, answer2_options, answer3_type, instructions, estimated_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data.get('task_name'), data.get('class_level'), data.get('difficulty_level'),
                        data.get('problem_text'), data.get('question1'), data.get('question2'), data.get('question3'),
                        _json.dumps(data.get('answer1_options') or []), _json.dumps(data.get('answer2_options') or []),
                        data.get('answer3_type'), data.get('instructions'), data.get('estimated_time')
                    )
                )
            elif category_slug == 'aptitude':
                import json as _json
                # Detect schema and insert accordingly
                cursor2 = conn.cursor(dictionary=True)
                cursor2.execute("SHOW COLUMNS FROM aptitude_tasks")
                existing_columns = {row['Field'] for row in cursor2.fetchall()}
                cursor2.close()
                if 'logical_reasoning_questions' in existing_columns:
                    def section_from(prefix):
                        q1 = data.get(f'{prefix}_question1')
                        q2 = data.get(f'{prefix}_question2')
                        o1 = data.get(f'{prefix}_question1_options') or []
                        o2 = data.get(f'{prefix}_question2_options') or []
                        sec = []
                        if q1:
                            sec.append({'question': q1, 'options': o1})
                        if q2:
                            sec.append({'question': q2, 'options': o2})
                        return _json.dumps(sec)
                    cursor.execute(
                        """
                        INSERT INTO aptitude_tasks (
                            task_name, class_level, difficulty_level,
                            logical_reasoning_questions, numerical_ability_questions, verbal_ability_questions, spatial_reasoning_questions,
                            instructions, estimated_time
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            data.get('task_name'), data.get('class_level'), data.get('difficulty_level'),
                            section_from('logical'), section_from('numerical'), section_from('verbal'), section_from('spatial'),
                            data.get('instructions'), data.get('estimated_time')
                        )
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO aptitude_tasks (
                            task_name, class_level, difficulty_level, instructions, estimated_time, example,
                            logical_question1, logical_question1_options, logical_question2, logical_question2_options,
                            numerical_question1, numerical_question1_options, numerical_question2, numerical_question2_options,
                            verbal_question1, verbal_question1_options, verbal_question2, verbal_question2_options,
                            spatial_question1, spatial_question1_options, spatial_question2, spatial_question2_options
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            data.get('task_name'), data.get('class_level'), data.get('difficulty_level'),
                            data.get('instructions'), data.get('estimated_time'), data.get('example'),
                            data.get('logical_question1'), _json.dumps(data.get('logical_question1_options') or []),
                            data.get('logical_question2'), _json.dumps(data.get('logical_question2_options') or []),
                            data.get('numerical_question1'), _json.dumps(data.get('numerical_question1_options') or []),
                            data.get('numerical_question2'), _json.dumps(data.get('numerical_question2_options') or []),
                            data.get('verbal_question1'), _json.dumps(data.get('verbal_question1_options') or []),
                            data.get('verbal_question2'), _json.dumps(data.get('verbal_question2_options') or []),
                            data.get('spatial_question1'), _json.dumps(data.get('spatial_question1_options') or []),
                            data.get('spatial_question2'), _json.dumps(data.get('spatial_question2_options') or [])
                        )
                    )
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Admin category POST error: {e}")
        return jsonify({'success': False, 'message': 'Failed to save task'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/admin/categories/<string:category_slug>/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
def admin_category_task_detail(category_slug: str, task_id: int):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    cfg = _category_config(category_slug)
    if not cfg:
        return jsonify({'success': False, 'message': 'Unknown category'}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor()
        table = cfg['table']
        if request.method == 'DELETE':
            cursor.execute(f"DELETE FROM {table} WHERE id = %s", (task_id,))
            conn.commit()
            return jsonify({'success': True})
        elif request.method == 'GET':
            # Single task fetch, with schema normalization for aptitude
            getc = conn.cursor(dictionary=True)
            getc.execute(f"SELECT * FROM {table} WHERE id = %s", (task_id,))
            row = getc.fetchone()
            getc.close()
            if not row:
                return jsonify({'success': False, 'message': 'Task not found'}), 404
            if category_slug == 'aptitude':
                import json as _json
                normalized = dict(row)
                if 'logical_question1' not in row:
                    # JSON-based schema; fan-out to the fields admin editor expects
                    def parse_section(json_text):
                        try:
                            if isinstance(json_text, str):
                                return _json.loads(json_text) or []
                            return json_text or []
                        except Exception:
                            return []
                    lr = parse_section(row.get('logical_reasoning_questions'))
                    na = parse_section(row.get('numerical_ability_questions'))
                    va = parse_section(row.get('verbal_ability_questions'))
                    sr = parse_section(row.get('spatial_reasoning_questions'))
                    def add_pair(prefix, arr):
                        q1 = arr[0] if len(arr) > 0 else {}
                        q2 = arr[1] if len(arr) > 1 else {}
                        normalized[f'{prefix}_question1'] = q1.get('question')
                        normalized[f'{prefix}_question2'] = q2.get('question')
                        normalized[f'{prefix}_question1_options'] = q1.get('options') or []
                        normalized[f'{prefix}_question2_options'] = q2.get('options') or []
                    add_pair('logical', lr)
                    add_pair('numerical', na)
                    add_pair('verbal', va)
                    add_pair('spatial', sr)
                return jsonify({'success': True, 'task': normalized})
            else:
                return jsonify({'success':True,'task':row})
        else:
            # Partial update: fetch existing row first and merge
            data = request.get_json() or {}
            curd = conn.cursor(dictionary=True)
            curd.execute(f"SELECT * FROM {table} WHERE id = %s", (task_id,))
            existing = curd.fetchone() or {}
            curd.close()
            if category_slug == 'reading-aloud':
                cursor.execute(
                    """
                    UPDATE reading_tasks SET task_name=%s, age_min=%s, age_max=%s, difficulty_level=%s, content=%s, instructions=%s, estimated_time=%s WHERE id=%s
                    """,
                    (
                        existing.get('task_name'), existing.get('age_min'), existing.get('age_max'), existing.get('difficulty_level'),
                        data.get('content', existing.get('content')), data.get('instructions', existing.get('instructions')), data.get('estimated_time', existing.get('estimated_time')), task_id
                    )
                )
            elif category_slug == 'typing':
                cursor.execute(
                    """
                    UPDATE typing_tasks SET task_name=%s, age_min=%s, age_max=%s, difficulty_level=%s, prompt=%s, instructions=%s, word_limit_min=%s, word_limit_max=%s, estimated_time=%s WHERE id=%s
                    """,
                    (
                        existing.get('task_name'), existing.get('age_min'), existing.get('age_max'), existing.get('difficulty_level'),
                        data.get('prompt', existing.get('prompt')), data.get('instructions', existing.get('instructions')), data.get('word_limit_min', existing.get('word_limit_min')), data.get('word_limit_max', existing.get('word_limit_max')), data.get('estimated_time', existing.get('estimated_time')), task_id
                    )
                )
            elif category_slug == 'writing':
                cursor.execute(
                    """
                    UPDATE writing_tasks SET task_name=%s, age_min=%s, age_max=%s, difficulty_level=%s, prompt=%s, instructions=%s, word_limit_min=%s, word_limit_max=%s, estimated_time=%s WHERE id=%s
                    """,
                    (
                        existing.get('task_name'), existing.get('age_min'), existing.get('age_max'), existing.get('difficulty_level'),
                        data.get('prompt', existing.get('prompt')), data.get('instructions', existing.get('instructions')), data.get('word_limit_min', existing.get('word_limit_min')), data.get('word_limit_max', existing.get('word_limit_max')), data.get('estimated_time', existing.get('estimated_time')), task_id
                    )
                )
            elif category_slug == 'reading-comprehension':
                import json as _json
                cursor.execute(
                    """
                    UPDATE reading_comprehension_tasks SET task_name=%s, age_min=%s, age_max=%s, difficulty_level=%s, passage=%s, question1=%s, question2=%s, question3=%s, answer1_options=%s, answer2_options=%s, answer3_type=%s, instructions=%s, estimated_time=%s WHERE id=%s
                    """,
                    (
                        existing.get('task_name'), existing.get('age_min'), existing.get('age_max'), existing.get('difficulty_level'), data.get('passage', existing.get('passage')),
                        data.get('question1', existing.get('question1')), data.get('question2', existing.get('question2')), data.get('question3', existing.get('question3')), _json.dumps(data.get('answer1_options', existing.get('answer1_options') or [])), _json.dumps(data.get('answer2_options', existing.get('answer2_options') or [])),
                        existing.get('answer3_type'), data.get('instructions', existing.get('instructions')), data.get('estimated_time', existing.get('estimated_time')), task_id
                    )
                )
            elif category_slug == 'mathematical-comprehension':
                import json as _json
                cursor.execute(
                    """
                    UPDATE mathematical_comprehension_tasks SET task_name=%s, age_min=%s, age_max=%s, difficulty_level=%s, problem_text=%s, question1=%s, question2=%s, question3=%s, answer1_options=%s, answer2_options=%s, answer3_type=%s, instructions=%s, estimated_time=%s WHERE id=%s
                    """,
                    (
                        existing.get('task_name'), existing.get('age_min'), existing.get('age_max'), existing.get('difficulty_level'), data.get('problem_text', existing.get('problem_text')),
                        data.get('question1', existing.get('question1')), data.get('question2', existing.get('question2')), data.get('question3', existing.get('question3')), _json.dumps(data.get('answer1_options', existing.get('answer1_options') or [])), _json.dumps(data.get('answer2_options', existing.get('answer2_options') or [])),
                        existing.get('answer3_type'), data.get('instructions', existing.get('instructions')), data.get('estimated_time', existing.get('estimated_time')), task_id
                    )
                )
            elif category_slug == 'aptitude':
                import json as _json
                # Detect schema and update accordingly
                chk = conn.cursor(dictionary=True)
                chk.execute("SHOW COLUMNS FROM aptitude_tasks")
                existing_columns = {row['Field'] for row in chk.fetchall()}
                chk.close()
                if 'logical_reasoning_questions' in existing_columns:
                    # Build section arrays from incoming or existing values
                    def section_from(prefix):
                        # Prefer incoming discrete fields, else try to reconstruct from existing JSON
                        q1 = data.get(f'{prefix}_question1')
                        q2 = data.get(f'{prefix}_question2')
                        o1 = data.get(f'{prefix}_question1_options')
                        o2 = data.get(f'{prefix}_question2_options')
                        if q1 is None and q2 is None and o1 is None and o2 is None:
                            # Use existing JSON
                            raw = existing.get({
                                'logical': 'logical_reasoning_questions',
                                'numerical': 'numerical_ability_questions',
                                'verbal': 'verbal_ability_questions',
                                'spatial': 'spatial_reasoning_questions'
                            }[prefix])
                            try:
                                if isinstance(raw, str):
                                    return raw  # already JSON string
                                return _json.dumps(raw or [])
                            except Exception:
                                return _json.dumps([])
                        # Build from incoming
                        sec = []
                        if q1:
                            sec.append({'question': q1, 'options': o1 or []})
                        if q2:
                            sec.append({'question': q2, 'options': o2 or []})
                        return _json.dumps(sec)
                    cursor.execute(
                        """
                        UPDATE aptitude_tasks SET 
                            task_name=%s, age_min=%s, age_max=%s, difficulty_level=%s,
                            logical_reasoning_questions=%s, numerical_ability_questions=%s, verbal_ability_questions=%s, spatial_reasoning_questions=%s,
                            instructions=%s, estimated_time=%s
                        WHERE id=%s
                        """,
                        (
                            existing.get('task_name'), existing.get('age_min'), existing.get('age_max'), existing.get('difficulty_level'),
                            section_from('logical'), section_from('numerical'), section_from('verbal'), section_from('spatial'),
                            data.get('instructions', existing.get('instructions')), data.get('estimated_time', existing.get('estimated_time')),
                            task_id
                        )
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE aptitude_tasks SET 
                            task_name=%s, age_min=%s, age_max=%s, difficulty_level=%s, instructions=%s, estimated_time=%s, example=%s,
                            logical_question1=%s, logical_question1_options=%s, logical_question2=%s, logical_question2_options=%s,
                            numerical_question1=%s, numerical_question1_options=%s, numerical_question2=%s, numerical_question2_options=%s,
                            verbal_question1=%s, verbal_question1_options=%s, verbal_question2=%s, verbal_question2_options=%s,
                            spatial_question1=%s, spatial_question1_options=%s, spatial_question2=%s, spatial_question2_options=%s
                        WHERE id=%s
                        """,
                        (
                            existing.get('task_name'), existing.get('age_min'), existing.get('age_max'), existing.get('difficulty_level'),
                            data.get('instructions', existing.get('instructions')), data.get('estimated_time', existing.get('estimated_time')), 
                            data.get('example', existing.get('example')),
                            data.get('logical_question1', existing.get('logical_question1')), _json.dumps(data.get('logical_question1_options', existing.get('logical_question1_options') or [])),
                            data.get('logical_question2', existing.get('logical_question2')), _json.dumps(data.get('logical_question2_options', existing.get('logical_question2_options') or [])),
                            data.get('numerical_question1', existing.get('numerical_question1')), _json.dumps(data.get('numerical_question1_options', existing.get('numerical_question1_options') or [])),
                            data.get('numerical_question2', existing.get('numerical_question2')), _json.dumps(data.get('numerical_question2_options', existing.get('numerical_question2_options') or [])),
                            data.get('verbal_question1', existing.get('verbal_question1')), _json.dumps(data.get('verbal_question1_options', existing.get('verbal_question1_options') or [])),
                            data.get('verbal_question2', existing.get('verbal_question2')), _json.dumps(data.get('verbal_question2_options', existing.get('verbal_question2_options') or [])),
                            data.get('spatial_question1', existing.get('spatial_question1')), _json.dumps(data.get('spatial_question1_options', existing.get('spatial_question1_options') or [])),
                            data.get('spatial_question2', existing.get('spatial_question2')), _json.dumps(data.get('spatial_question2_options', existing.get('spatial_question2_options') or [])),
                            task_id
                        )
                    )
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Admin category PUT/DELETE error: {e}")
        return jsonify({'success': False, 'message': 'Failed to update task'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/admin/categories/<string:category_slug>/tasks/<int:task_id>', methods=['GET'])
def admin_category_task_get(category_slug: str, task_id: int):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    cfg = _category_config(category_slug)
    if not cfg:
        return jsonify({'success': False, 'message': 'Unknown category'}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {cfg['table']} WHERE id=%s", (task_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        return jsonify({'success': True, 'task': row})
    except Exception as e:
        print(f"Admin get single task error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch task'}), 500


# Random task selection for Reading Aloud
@app.route('/api/reading-tasks-random/<int:user_id>', methods=['GET'])
def get_random_reading_task(user_id: int):
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        # Resolve age
        cursor.execute("SELECT age, date_of_birth FROM demographics WHERE user_id = %s", (user_id,))
        demo = cursor.fetchone()
        from datetime import datetime
        user_age = None
        if demo:
            if demo.get('age'):
                user_age = demo['age']
            elif demo.get('date_of_birth'):
                today = datetime.now()
                dob = demo['date_of_birth']
                user_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if not user_age:
            # fallback to any
            cursor.execute("SELECT id FROM reading_tasks ORDER BY RAND() LIMIT 1")
        else:
            cursor.execute("""
                SELECT id FROM reading_tasks WHERE age_min <= %s AND age_max >= %s ORDER BY RAND() LIMIT 1
            """, (user_age, user_age))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return jsonify({'success': False, 'message': 'No reading tasks available'}), 404
        return jsonify({'success': True, 'task_id': row['id']})
    except Exception as e:
        print(f"Random reading task error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get random task'}), 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        # Simple hardcoded admin credentials (replace with DB check in production)
        if username == 'admin' and password == 'admin123':
            session['is_admin'] = True
            # flash('Admin login successful!', 'success')
            return redirect(url_for('admin_portal'))
        else:
            flash('Invalid admin credentials', 'error')
            return render_template('admin_login.html')
    return render_template('admin_login.html')

# --- Task status API ---
@app.route('/api/user-tasks', methods=['GET'])
def get_user_tasks():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT task_name, status FROM user_tasks WHERE user_id = %s"
        cursor.execute(query, (session['user_id'],))
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        print(f"Get user tasks error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch tasks'}), 500

# --- Student: allowed tasks for dashboard (strict by class/section) ---
@app.route('/api/allowed-tasks', methods=['GET'])
def api_allowed_tasks():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    try:
        user_id = session['user_id']
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        # Determine if school child
        cursor.execute("SELECT section_id, school_id FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        section_id = row['section_id'] if row else None
        school_id = row['school_id'] if row else None

        tasks = []
        
        # Get user's class level from demographics
        class_level = _get_user_class_level(conn, user_id)
        
        if class_level:
            # Show class-appropriate tasks based on class level
            allowed = []
            
            # Check each task category for class-appropriate content
            task_categories = [
                ('Reading Aloud Task 1', 'reading_tasks'),
                ('Typing Task', 'typing_tasks'), 
                ('Reading Comprehension', 'reading_comprehension_tasks'),
                ('Mathematical Comprehension', 'mathematical_comprehension_tasks'),
                ('Writing Task', 'writing_tasks'),
                ('Aptitude Test', 'aptitude_tasks')
            ]
            
            for task_name, table_name in task_categories:
                # Check if there are class-appropriate tasks for this category
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name} WHERE class_level = %s", (class_level,))
                count_result = cursor.fetchone()
                if count_result and count_result['count'] > 0:
                    allowed.append(task_name)
            
            # If no class-specific tasks found, show all core tasks as fallback
            if not allowed:
                cursor.execute("SELECT task_name FROM tasks ORDER BY id")
                allowed = [r['task_name'] for r in cursor.fetchall()]
        else:
            # No class level found: show all tasks as fallback
            cursor.execute("SELECT task_name FROM tasks ORDER BY id")
            allowed = [r['task_name'] for r in cursor.fetchall()]

        # Map with user status
        cursor.execute("SELECT task_name, status FROM user_tasks WHERE user_id = %s", (user_id,))
        status_map = {r['task_name']: r['status'] for r in cursor.fetchall()}
        for name in allowed:
            tasks.append({'task_name': name, 'status': status_map.get(name, 'Not Started')})

        cursor.close(); conn.close()
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        print(f"Allowed tasks API error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch allowed tasks'}), 500

@app.route('/api/user-tasks', methods=['POST'])
def update_user_task():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    data = request.get_json()
    task_name = data.get('task_name')
    status = data.get('status')
    if not task_name or status not in ['Not Started', 'In Progress', 'Completed']:
        return jsonify({'success': False, 'message': 'Invalid task or status'}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor()
        # Upsert logic: update if exists, else insert
        query = """
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        """
        cursor.execute(query, (session['user_id'], task_name, status))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Task status updated'})
    except Exception as e:
        print(f"Update user task error: {e}")
        return jsonify({'success': False, 'message': 'Failed to update task'}), 500

@app.route('/profile', methods=['GET'])
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    # Fetch user details from users and demographics
    user = None
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        query = '''
            SELECT u.name, u.email, d.date_of_birth, d.gender, d.native_language, d.education_level, d.dyslexia_status
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
            WHERE u.id = %s
        '''
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Profile fetch error: {e}")
    return render_template('profile.html', user=user)

@app.route('/api/profile', methods=['POST'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    dob = data.get('date_of_birth', '').strip()
    gender = data.get('gender', '').strip()
    native_language = data.get('native_language', '').strip()
    education_level = data.get('education_level', '').strip()
    dyslexia_status = data.get('dyslexia_status', '').strip()
    if not name or not email:
        return jsonify({'success': False, 'message': 'Name and email are required'}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor()
        # Update users table
        if password:
            import bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("UPDATE users SET name = %s, email = %s, password_hash = %s WHERE id = %s", (name, email, password_hash, user_id))
        else:
            cursor.execute("UPDATE users SET name = %s, email = %s WHERE id = %s", (name, email, user_id))
        # Update or insert demographics
        cursor.execute("SELECT id FROM demographics WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE demographics SET date_of_birth = %s, gender = %s, native_language = %s, education_level = %s, dyslexia_status = %s WHERE user_id = %s
            """, (dob, gender, native_language, education_level, dyslexia_status, user_id))
        else:
            cursor.execute("""
                INSERT INTO demographics (user_id, date_of_birth, gender, native_language, education_level, dyslexia_status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, dob, gender, native_language, education_level, dyslexia_status))
        conn.commit()
        cursor.close()
        conn.close()
        session['email'] = email
        return jsonify({'success': True, 'message': 'Profile updated'})
    except Exception as e:
        print(f"Profile update error: {e}")
        return jsonify({'success': False, 'message': 'Failed to update profile'}), 500

@app.route('/task1.html')
def task1():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task1.html', user_id=user_id)

@app.route('/task2.html')
def task2():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task2.html', user_id=user_id)

@app.route('/task3.html')
def task3():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task3.html', user_id=user_id)

@app.route('/task4.html')
def task4():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task4.html', user_id=user_id)

@app.route('/task11.html')
def task11():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task11.html', user_id=user_id)

@app.route('/task22.html')
def task22():
    return render_template('task22.html')

@app.route('/task33.html')
def task33():
    return render_template('task33.html')

@app.route('/task44.html')
def task44():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task44.html', user_id=user_id)

@app.route('/task5.html')
def task5():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task5.html', user_id=user_id)

@app.route('/task55.html')
def task55():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task55.html', user_id=user_id)

@app.route('/task6.html')
def task6():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))
    return render_template('task6.html', user_id=user_id)

@app.route('/aptitude.html')
def aptitude():
    # Require login to access the aptitude test so progress can be saved to a user
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    return render_template('aptitude.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/save-progress', methods=['POST'])
def save_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    if 'audio' not in request.files:
        return jsonify({'success': False, 'message': 'No audio file provided'}), 400
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    task_name = request.form.get('task_name', 'Reading Aloud Task 1')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"user{session['user_id']}_" + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            conn = connect_db()
            cursor = conn.cursor()
            
            # Get or create task attempt
            cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
            task_row = cursor.fetchone()
            if not task_row:
                return jsonify({'success': False, 'message': 'Task not found'}), 404
            
            task_id = task_row[0]
            
            # Get current attempt or create new one
            cursor.execute("""
                SELECT id, attempt_number FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
                ORDER BY attempt_number DESC LIMIT 1
            """, (session['user_id'], task_id))
            
            attempt_row = cursor.fetchone()
            if attempt_row:
                attempt_id = attempt_row[0]
                attempt_number = attempt_row[1]
            else:
                # Create new attempt
                cursor.execute("""
                    SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM user_task_attempts 
                    WHERE user_id = %s AND task_id = %s
                """, (session['user_id'], task_id))
                attempt_number = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (session['user_id'], task_id, attempt_number, 'In Progress'))
                attempt_id = cursor.lastrowid
            
            # Save audio recording with attempt_id
            cursor.execute("""
                INSERT INTO audio_recordings (attempt_id, filename, uploaded_at)
                VALUES (%s, %s, NOW())
            """, (attempt_id, filename))
            
            # Mark task as In Progress
            cursor.execute("""
                INSERT INTO user_tasks (user_id, task_name, status)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
            """, (session['user_id'], task_name, 'In Progress'))
            
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Progress saved successfully', 'filename': filename, 'attempt_id': attempt_id, 'attempt_number': attempt_number})
        except Exception as e:
            print(f"Save progress DB error: {e}")
            return jsonify({'success': False, 'message': 'Failed to save progress'}), 500
    else:
        return jsonify({'success': False, 'message': 'Invalid file type'}), 400

# @app.route('/api/upload-audio', methods=['POST'])
# def upload_audio():
#     if 'user_id' not in session:
#         return jsonify({'success': False, 'message': 'User not logged in'}), 401
#     if 'audio' not in request.files:
#         return jsonify({'success': False, 'message': 'No audio file provided'}), 400
#     file = request.files['audio']
#     if file.filename == '':
#         return jsonify({'success': False, 'message': 'No selected file'}), 400
#     if file and allowed_file(file.filename):
#         filename = secure_filename(f"user{session['user_id']}_" + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + file.filename)
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)
#         # Save metadata to DB and mark task as completed
#         try:
#             conn = connect_db()
#             cursor = conn.cursor()
#             # Insert audio recording
#             cursor.execute("""
#                 INSERT INTO audio_recordings (user_id, filename, uploaded_at)
#                 VALUES (%s, %s, NOW())
#             """, (session['user_id'], filename))
#             # Mark task as completed
#             cursor.execute("""
#                 INSERT INTO user_tasks (user_id, task_name, status)
#                 VALUES (%s, %s, %s)
#                 ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
#             """, (session['user_id'], 'Reading Aloud Task 1', 'Completed'))
#             conn.commit()
#             cursor.close()
#             conn.close()
#         except Exception as e:
#             print(f"Audio metadata DB error: {e}")
#         return jsonify({'success': True, 'message': 'Audio uploaded successfully and task marked as completed', 'filename': filename})
#     else:
#         return jsonify({'success': False, 'message': 'Invalid file type'}), 400



@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Upload audio recording and mark task as completed"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if 'audio' not in request.files:
        return jsonify({'success': False, 'message': 'No audio file provided'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    task_name = request.form.get('task_name', 'Reading Aloud Task 1')
    is_retake = request.form.get('retake') == 'true'
    
    if file and allowed_file(file.filename):
        # Generate a unique filename including timestamp to preserve all submissions
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = secure_filename(f"user{session['user_id']}_{timestamp}_{'retake_' if is_retake else ''}{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            conn = connect_db()
            cursor = conn.cursor()
            
            # Get or create task attempt
            cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
            task_row = cursor.fetchone()
            if not task_row:
                return jsonify({'success': False, 'message': 'Task not found'}), 404
            
            task_id = task_row[0]
            
            # Get current attempt or create new one
            cursor.execute("""
                SELECT id, attempt_number FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
                ORDER BY attempt_number DESC LIMIT 1
            """, (session['user_id'], task_id))
            
            attempt_row = cursor.fetchone()
            if attempt_row:
                attempt_id = attempt_row[0]
                attempt_number = attempt_row[1]
            else:
                # Create new attempt
                cursor.execute("""
                    SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM user_task_attempts 
                    WHERE user_id = %s AND task_id = %s
                """, (session['user_id'], task_id))
                attempt_number = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (session['user_id'], task_id, attempt_number, 'In Progress'))
                attempt_id = cursor.lastrowid
            
            # Save audio recording with attempt_id
            cursor.execute("""
                INSERT INTO audio_recordings (attempt_id, filename, uploaded_at)
                VALUES (%s, %s, NOW())
            """, (attempt_id, filename))
            
            # Mark attempt as completed
            cursor.execute("""
                UPDATE user_task_attempts 
                SET status = 'Completed', completed_at = NOW()
                WHERE id = %s
            """, (attempt_id,))
            
            # Mark user_tasks as Completed
            cursor.execute("""
                INSERT INTO user_tasks (user_id, task_name, status)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
            """, (session['user_id'], task_name, 'Completed'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': 'Audio uploaded successfully and task marked as completed',
                'filename': filename,
                'attempt_id': attempt_id,
                'attempt_number': attempt_number
            })
        except Exception as e:
            print(f"Upload audio error: {e}")
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'Invalid file type'}), 400
    
    
@app.route('/api/retake-task', methods=['POST'])
def retake_task():
    """Create a new attempt for retaking while preserving previous submissions"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    task_name = data.get('task_name', 'Reading Aloud Task 1')
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row[0]
        
        # Get next attempt number
        cursor.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s
        """, (session['user_id'], task_id))
        attempt_number = cursor.fetchone()[0]
        
        # Create new attempt
        cursor.execute("""
            INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (session['user_id'], task_id, attempt_number, 'In Progress'))
        attempt_id = cursor.lastrowid
        
        # Mark user_tasks as In Progress
        cursor.execute("""
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        """, (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'New attempt created for retake. Previous submissions preserved.',
            'attempt_id': attempt_id,
            'attempt_number': attempt_number,
            'task_name': task_name
        })
    except Exception as e:
        print(f"Error creating retake attempt: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/get-saved-progress', methods=['GET'])
def get_saved_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    task_name = request.args.get('task_name', 'Reading Aloud Task 1')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get the latest IN PROGRESS attempt and its audio recording (not completed ones)
        # Order by audio uploaded_at to get the most recent saved audio
        cursor.execute("""
            SELECT 
                uta.id as attempt_id,
                uta.attempt_number,
                uta.status as attempt_status,
                uta.started_at,
                uta.completed_at,
                ar.filename, ar.uploaded_at
            FROM user_task_attempts uta
            LEFT JOIN audio_recordings ar ON ar.attempt_id = uta.id
            WHERE uta.user_id = %s AND uta.task_id = %s AND uta.status = 'In Progress'
            ORDER BY ar.uploaded_at DESC
            LIMIT 1
        """, (session['user_id'], task_id))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result.get('filename'):
            audio_url = f"/uploads/{result['filename']}"
            return jsonify({
                'success': True, 
                'saved_audio': audio_url,
                'attempt_id': result.get('attempt_id'),
                'attempt_number': result.get('attempt_number'),
                'attempt_status': result.get('attempt_status'),
                'started_at': result.get('started_at'),
                'completed_at': result.get('completed_at')
            })
        else:
            return jsonify({'success': True, 'saved_audio': None})
    except Exception as e:
        print(f"Get saved progress error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get saved progress'}), 500

@app.route('/api/save-typing-progress', methods=['POST'])
def save_typing_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    data = request.get_json()
    text = data.get('text', '')
    keystrokes = data.get('keystrokes', '')
    timer = data.get('timer', '')
    task_name = data.get('task_name', 'Typing Task')
    if not text:
        return jsonify({'success': False, 'message': 'No text provided'}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get or create task attempt - handle both main tasks and typing tasks
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        
        if not task_row:
            # If not found in main tasks table, try typing_tasks table
            cursor.execute("SELECT id FROM typing_tasks WHERE task_name = %s", (task_name,))
            typing_task_row = cursor.fetchone()
            if typing_task_row:
                # For typing tasks, we need to use the main "Typing Task" as the parent task
                cursor.execute("SELECT id FROM tasks WHERE task_name = 'Typing Task'")
                main_task_row = cursor.fetchone()
                if main_task_row:
                    task_id = main_task_row[0]
                else:
                    return jsonify({'success': False, 'message': 'Typing Task not found in main tasks'}), 404
            else:
                return jsonify({'success': False, 'message': 'Task not found'}), 404
        else:
            task_id = task_row[0]
        
        # Get current attempt or create new one
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if attempt_row:
            attempt_id = attempt_row[0]
            attempt_number = attempt_row[1]
        else:
            # Create new attempt
            cursor.execute("""
                SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s
            """, (session['user_id'], task_id))
            attempt_number = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (session['user_id'], task_id, attempt_number, 'In Progress'))
            attempt_id = cursor.lastrowid
        
        # Save progress to typing_progress table
        cursor.execute('''
            INSERT INTO typing_progress (attempt_id, text, keystrokes, timer, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE text=VALUES(text), keystrokes=VALUES(keystrokes), timer=VALUES(timer), updated_at=NOW()
        ''', (attempt_id, text, keystrokes, timer))
        
        # Mark user_tasks as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Progress saved successfully', 'attempt_id': attempt_id, 'attempt_number': attempt_number})
    except Exception as e:
        print(f"Save typing progress DB error: {e}")
        return jsonify({'success': False, 'message': 'Failed to save progress'}), 500

@app.route('/api/submit-typing-task', methods=['POST'])
def submit_typing_task():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    data = request.get_json()
    text = data.get('text', '')
    keystrokes = data.get('keystrokes', '')
    timer = data.get('timer', '')
    task_name = data.get('task_name', 'Typing Task')
    if not text:
        return jsonify({'success': False, 'message': 'No text provided'}), 400
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get or create task attempt - handle both main tasks and typing tasks
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        
        if not task_row:
            # If not found in main tasks table, try typing_tasks table
            cursor.execute("SELECT id FROM typing_tasks WHERE task_name = %s", (task_name,))
            typing_task_row = cursor.fetchone()
            if typing_task_row:
                # For typing tasks, we need to use the main "Typing Task" as the parent task
                cursor.execute("SELECT id FROM tasks WHERE task_name = 'Typing Task'")
                main_task_row = cursor.fetchone()
                if main_task_row:
                    task_id = main_task_row[0]
                else:
                    return jsonify({'success': False, 'message': 'Typing Task not found in main tasks'}), 404
            else:
                return jsonify({'success': False, 'message': 'Task not found'}), 404
        else:
            task_id = task_row[0]
        
        # Get current attempt or create new one
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if attempt_row:
            attempt_id = attempt_row[0]
            attempt_number = attempt_row[1]
        else:
            # Create new attempt
            cursor.execute("""
                SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s
            """, (session['user_id'], task_id))
            attempt_number = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (session['user_id'], task_id, attempt_number, 'In Progress'))
            attempt_id = cursor.lastrowid
        
        # Save final progress to typing_progress table
        cursor.execute('''
            INSERT INTO typing_progress (attempt_id, text, keystrokes, timer, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE text=VALUES(text), keystrokes=VALUES(keystrokes), timer=VALUES(timer), updated_at=NOW()
        ''', (attempt_id, text, keystrokes, timer))
        
        # Mark attempt as completed
        cursor.execute("""
            UPDATE user_task_attempts 
            SET status = 'Completed', completed_at = NOW()
            WHERE id = %s
        """, (attempt_id,))
        
        # Mark user_tasks as Completed
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'Completed'))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Task submitted and marked as completed', 'attempt_id': attempt_id, 'attempt_number': attempt_number})
    except Exception as e:
        print(f"Submit typing task DB error: {e}")
        return jsonify({'success': False, 'message': 'Failed to submit task'}), 500

@app.route('/api/get-typing-progress', methods=['GET'])
def get_typing_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    task_name = request.args.get('task_name', 'Typing Task')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get the latest IN PROGRESS attempt and its progress (not completed ones)
        # Order by progress updated_at to get the most recent saved progress
        cursor.execute("""
            SELECT 
                uta.id as attempt_id,
                uta.attempt_number,
                uta.status as attempt_status,
                uta.started_at,
                uta.completed_at,
                tp.text, tp.keystrokes, tp.timer, tp.updated_at
            FROM user_task_attempts uta
            LEFT JOIN typing_progress tp ON tp.attempt_id = uta.id
            WHERE uta.user_id = %s AND uta.task_id = %s AND uta.status = 'In Progress'
            ORDER BY tp.updated_at DESC
            LIMIT 1
        """, (session['user_id'], task_id))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result.get('text'):
            return jsonify({
                'success': True,
                'progress': {
                    'text': result.get('text', ''),
                    'keystrokes': result.get('keystrokes', ''),
                    'timer': result.get('timer', 0),
                    'updated_at': result.get('updated_at'),
                    'attempt_id': result.get('attempt_id'),
                    'attempt_number': result.get('attempt_number'),
                    'attempt_status': result.get('attempt_status'),
                    'started_at': result.get('started_at'),
                    'completed_at': result.get('completed_at')
                }
            })
        else:
            return jsonify({'success': True, 'progress': None})
    except Exception as e:
        print(f"Get typing progress error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get progress'}), 500

@app.route('/api/retake-typing', methods=['POST'])
def retake_typing():
    """Create a new attempt for typing task"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    data = request.get_json()
    task_name = data.get('task_name', 'Typing Task')

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404

        task_id = task_row[0]

        # Get next attempt number
        cursor.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s
        """, (session['user_id'], task_id))
        attempt_number = cursor.fetchone()[0]

        # Create new attempt
        cursor.execute("""
            INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (session['user_id'], task_id, attempt_number, 'In Progress'))
        attempt_id = cursor.lastrowid

        # Mark user_tasks as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'In Progress'))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'New attempt created', 'attempt_id': attempt_id, 'attempt_number': attempt_number})
    except Exception as e:
        print(f"Retake typing DB error: {e}")
        return jsonify({'success': False, 'message': 'Failed to create new attempt'}), 500

@app.route('/api/save-comprehension-progress', methods=['POST'])
def save_comprehension_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    data = request.get_json()
    q1 = data.get('q1', '')
    q2 = data.get('q2', '')
    q3 = data.get('q3', '')
    task_name = data.get('task_name', 'Reading Comprehension')
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get or create task attempt
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row[0]
        
        # Get current attempt or create new one
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if attempt_row:
            attempt_id = attempt_row[0]
            attempt_number = attempt_row[1]
        else:
            # Create new attempt
            cursor.execute("""
                SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s
            """, (session['user_id'], task_id))
            attempt_number = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (session['user_id'], task_id, attempt_number, 'In Progress'))
            attempt_id = cursor.lastrowid
        
        # Save progress to comprehension_progress table
        cursor.execute('''
            INSERT INTO comprehension_progress (attempt_id, q1, q2, q3, status, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE q1=VALUES(q1), q2=VALUES(q2), q3=VALUES(q3), status=VALUES(status), updated_at=NOW()
        ''', (attempt_id, q1, q2, q3, 'In Progress'))
        
        # Mark user_tasks as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Progress saved successfully', 'attempt_id': attempt_id, 'attempt_number': attempt_number})
    except Exception as e:
        print(f"Save comprehension progress DB error: {e}")
        return jsonify({'success': False, 'message': 'Failed to save progress'}), 500

@app.route('/api/get-comprehension-progress', methods=['GET'])
def get_comprehension_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    task_name = request.args.get('task_name', 'Reading Comprehension')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get the latest IN PROGRESS attempt and its progress (not completed ones)
        # Order by progress updated_at to get the most recent saved progress
        cursor.execute('''
            SELECT 
                uta.id as attempt_id,
                uta.attempt_number,
                uta.status as attempt_status,
                uta.started_at,
                uta.completed_at,
                cp.q1, cp.q2, cp.q3, cp.status as progress_status, cp.updated_at
            FROM user_task_attempts uta
            LEFT JOIN comprehension_progress cp ON cp.attempt_id = uta.id
            WHERE uta.user_id = %s AND uta.task_id = %s AND uta.status = 'In Progress'
            ORDER BY cp.updated_at DESC
            LIMIT 1
        ''', (session['user_id'], task_id))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                'success': True, 
                'progress': {
                    'q1': result.get('q1', ''),
                    'q2': result.get('q2', ''),
                    'q3': result.get('q3', ''),
                    'status': result.get('progress_status', 'In Progress'),
                    'attempt_id': result.get('attempt_id'),
                    'attempt_number': result.get('attempt_number'),
                    'attempt_status': result.get('attempt_status'),
                    'started_at': result.get('started_at'),
                    'completed_at': result.get('completed_at')
                }
            })
        else:
            return jsonify({'success': True, 'progress': None})
    except Exception as e:
        print(f"Get comprehension progress error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get progress'}), 500

@app.route('/api/submit-comprehension', methods=['POST'])
def submit_comprehension():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    data = request.get_json()
    q1 = data.get('q1', '')
    q2 = data.get('q2', '')
    q3 = data.get('q3', '')
    task_name = data.get('task_name', 'Reading Comprehension')
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get or create task attempt
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row[0]
        
        # Get current attempt or create new one
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if attempt_row:
            attempt_id = attempt_row[0]
            attempt_number = attempt_row[1]
        else:
            # Create new attempt
            cursor.execute("""
                SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s
            """, (session['user_id'], task_id))
            attempt_number = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (session['user_id'], task_id, attempt_number, 'In Progress'))
            attempt_id = cursor.lastrowid
        
        # Save final progress to comprehension_progress table
        cursor.execute('''
            INSERT INTO comprehension_progress (attempt_id, q1, q2, q3, status, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE q1=VALUES(q1), q2=VALUES(q2), q3=VALUES(q3), status=VALUES(status), updated_at=NOW()
        ''', (attempt_id, q1, q2, q3, 'Completed'))
        
        # Mark attempt as completed
        cursor.execute("""
            UPDATE user_task_attempts 
            SET status = 'Completed', completed_at = NOW()
            WHERE id = %s
        """, (attempt_id,))
        
        # Mark user_tasks as Completed
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'Completed'))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Task submitted and marked as completed', 'attempt_id': attempt_id, 'attempt_number': attempt_number})
    except Exception as e:
        print(f"Submit comprehension DB error: {e}")
        return jsonify({'success': False, 'message': 'Failed to submit task'}), 500

@app.route('/api/retake-comprehension', methods=['POST'])
def retake_comprehension():
    """Create a new attempt for reading comprehension task"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_name = data.get('task_name', 'Reading Comprehension')
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row[0]
        
        # Get next attempt number
        cursor.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s
        """, (session['user_id'], task_id))
        attempt_number = cursor.fetchone()[0]
        
        # Create new attempt
        cursor.execute("""
            INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (session['user_id'], task_id, attempt_number, 'In Progress'))
        attempt_id = cursor.lastrowid
        
        # Mark user_tasks as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'New attempt created', 'attempt_id': attempt_id, 'attempt_number': attempt_number})
    except Exception as e:
        print(f"Retake comprehension DB error: {e}")
        return jsonify({'success': False, 'message': 'Failed to create new attempt'}), 500


@app.route('/api/save-aptitude-progress', methods=['POST'])
def save_aptitude_progress():
    """Save aptitude test progress using user_task_attempts system"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    print(f"Received aptitude save data: {data}")  # Debug logging
    
    task_name = data.get('task_name', 'Aptitude Test')
    logical_reasoning_score = data.get('logical_reasoning_score', 0)
    numerical_ability_score = data.get('numerical_ability_score', 0)
    verbal_ability_score = data.get('verbal_ability_score', 0)
    spatial_reasoning_score = data.get('spatial_reasoning_score', 0)
    total_score = data.get('total_score', 0)
    answers = data.get('answers')
    current_section = data.get('current_section')
    answered_count = data.get('answered_count', 0)
    progress_percent = data.get('progress_percent', 0)
    
    print(f"Parsed values - answers: {answers}, current_section: {current_section}, answered_count: {answered_count}")  # Debug logging
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get or create IN PROGRESS attempt
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if attempt_row:
            attempt_id = attempt_row['id']
            attempt_number = attempt_row['attempt_number']
        else:
            # Create new attempt
            cursor.execute("""
                SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt 
                FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s
            """, (session['user_id'], task_id))
            next_attempt = cursor.fetchone()['next_attempt']
            
            cursor.execute("""
                INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (session['user_id'], task_id, next_attempt, 'In Progress'))
            
            attempt_id = cursor.lastrowid
            attempt_number = next_attempt
        
        # Save/update aptitude progress
        # Handle JSON serialization properly
        answers_json = None
        if answers:
            try:
                answers_json = json.dumps(answers)
                print(f"Serialized answers JSON: {answers_json}")  # Debug logging
            except (TypeError, ValueError) as e:
                print(f"Error serializing answers: {e}")
                answers_json = None
        else:
            print("No answers to serialize")  # Debug logging
        
        # Debug the SQL parameters
        sql_params = (
            attempt_id, logical_reasoning_score, numerical_ability_score,
            verbal_ability_score, spatial_reasoning_score, total_score,
            'In Progress', answers_json,
            current_section, answered_count, progress_percent
        )
        print(f"SQL parameters: {sql_params}")  # Debug logging
        
        cursor.execute("""
            INSERT INTO aptitude_progress (
                attempt_id, logical_reasoning_score, numerical_ability_score, 
                verbal_ability_score, spatial_reasoning_score, total_score, 
                status, answers, current_section, answered_count, progress_percent, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                logical_reasoning_score=VALUES(logical_reasoning_score),
                numerical_ability_score=VALUES(numerical_ability_score),
                verbal_ability_score=VALUES(verbal_ability_score),
                spatial_reasoning_score=VALUES(spatial_reasoning_score),
                total_score=VALUES(total_score),
                status=VALUES(status),
                answers=VALUES(answers),
                current_section=VALUES(current_section),
                answered_count=VALUES(answered_count),
                progress_percent=VALUES(progress_percent),
                updated_at=NOW()
        """, sql_params)
        
        # Mark user_tasks as In Progress
        cursor.execute("""
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        """, (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Progress saved successfully',
            'attempt_id': attempt_id,
            'attempt_number': attempt_number
        })
    except Exception as e:
        print(f"Save aptitude progress error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/get-aptitude-progress', methods=['GET'])
def get_aptitude_progress():
    """Get aptitude test progress using user_task_attempts system"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    task_name = request.args.get('task_name', 'Aptitude Test')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get the latest IN PROGRESS attempt and its progress
        cursor.execute('''
            SELECT 
                uta.id as attempt_id,
                uta.attempt_number,
                uta.status as attempt_status,
                uta.started_at,
                uta.completed_at,
                ap.logical_reasoning_score, ap.numerical_ability_score, 
                ap.verbal_ability_score, ap.spatial_reasoning_score, 
                ap.total_score, ap.status as progress_status, 
                ap.answers, ap.current_section, ap.answered_count, 
                ap.progress_percent, ap.updated_at
            FROM user_task_attempts uta
            LEFT JOIN aptitude_progress ap ON ap.attempt_id = uta.id
            WHERE uta.user_id = %s AND uta.task_id = %s AND uta.status = 'In Progress'
            ORDER BY ap.updated_at DESC
            LIMIT 1
        ''', (session['user_id'], task_id))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result.get('attempt_id'):
            return jsonify({
                'success': True, 
                'progress': {
                    'attempt_id': result['attempt_id'],
                    'attempt_number': result['attempt_number'],
                    'logical_reasoning_score': result.get('logical_reasoning_score', 0),
                    'numerical_ability_score': result.get('numerical_ability_score', 0),
                    'verbal_ability_score': result.get('verbal_ability_score', 0),
                    'spatial_reasoning_score': result.get('spatial_reasoning_score', 0),
                    'total_score': result.get('total_score', 0),
                    'status': result.get('progress_status', 'In Progress'),
                    'answers': result.get('answers'),
                    'current_section': result.get('current_section'),
                    'answered_count': result.get('answered_count', 0),
                    'progress_percent': result.get('progress_percent', 0),
                    'updated_at': result.get('updated_at')
                }
            })
        else:
            return jsonify({'success': True, 'progress': None})
    except Exception as e:
        print(f"Get aptitude progress error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/submit-aptitude', methods=['POST'])
def submit_aptitude():
    """Submit aptitude test using user_task_attempts system"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_name = data.get('task_name', 'Aptitude Test')
    logical_reasoning_score = data.get('logical_reasoning_score', 0)
    numerical_ability_score = data.get('numerical_ability_score', 0)
    verbal_ability_score = data.get('verbal_ability_score', 0)
    spatial_reasoning_score = data.get('spatial_reasoning_score', 0)
    total_score = data.get('total_score', 0)
    answers = data.get('answers')
    current_section = data.get('current_section')
    answered_count = data.get('answered_count', 0)
    progress_percent = data.get('progress_percent', 0)
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get the latest IN PROGRESS attempt
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if not attempt_row:
            return jsonify({'success': False, 'message': 'No active attempt found'}), 404
        
        attempt_id = attempt_row['id']
        attempt_number = attempt_row['attempt_number']
        
        # Update aptitude progress to completed
        # Handle JSON serialization properly
        answers_json = None
        if answers:
            try:
                answers_json = json.dumps(answers)
            except (TypeError, ValueError) as e:
                print(f"Error serializing answers: {e}")
                answers_json = None
        
        cursor.execute("""
            INSERT INTO aptitude_progress (
                attempt_id, logical_reasoning_score, numerical_ability_score, 
                verbal_ability_score, spatial_reasoning_score, total_score, 
                status, answers, current_section, answered_count, progress_percent, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                logical_reasoning_score=VALUES(logical_reasoning_score),
                numerical_ability_score=VALUES(numerical_ability_score),
                verbal_ability_score=VALUES(verbal_ability_score),
                spatial_reasoning_score=VALUES(spatial_reasoning_score),
                total_score=VALUES(total_score),
                status='Completed',
                answers=VALUES(answers),
                current_section=VALUES(current_section),
                answered_count=VALUES(answered_count),
                progress_percent=VALUES(progress_percent),
                updated_at=NOW()
        """, (
            attempt_id, logical_reasoning_score, numerical_ability_score,
            verbal_ability_score, spatial_reasoning_score, total_score,
            'Completed', answers_json,
            current_section, answered_count, progress_percent
        ))
        
        # Mark attempt as completed
        cursor.execute("""
            UPDATE user_task_attempts 
            SET status = 'Completed', completed_at = NOW()
            WHERE id = %s
        """, (attempt_id,))
        
        # Mark user_tasks as Completed
        cursor.execute("""
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        """, (session['user_id'], task_name, 'Completed'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Test submitted successfully',
            'attempt_id': attempt_id,
            'attempt_number': attempt_number
        })
    except Exception as e:
        print(f"Submit aptitude error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/retake-aptitude', methods=['POST'])
def retake_aptitude():
    """Create a new attempt for aptitude test retake"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_name = data.get('task_name', 'Aptitude Test')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Create new attempt
        cursor.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt 
            FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s
        """, (session['user_id'], task_id))
        next_attempt = cursor.fetchone()['next_attempt']
        
        cursor.execute("""
            INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (session['user_id'], task_id, next_attempt, 'In Progress'))
        
        attempt_id = cursor.lastrowid
        
        # Mark user_tasks as In Progress
        cursor.execute("""
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        """, (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'New attempt created successfully',
            'attempt_id': attempt_id,
            'attempt_number': next_attempt
        })
    except Exception as e:
        print(f"Retake aptitude error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/reading-tasks/<int:user_id>', methods=['GET'])
def get_reading_tasks(user_id):
    """Get class-appropriate reading tasks for a user"""
    try:
        print(f"Fetching reading tasks for user_id: {user_id}")
        
        conn = connect_db()
        if not conn:
            print("Database connection failed")
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # First check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user_exists = cursor.fetchone()
        if not user_exists:
            print(f"User {user_id} not found")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Determine user's class level
        class_level = _get_user_class_level(conn, user_id)
        if not class_level:
            print("No class level; returning default reading tasks")
            return getDefaultReadingTasks()
        
        # Check if reading_tasks table exists
        cursor.execute("SHOW TABLES LIKE 'reading_tasks'")
        table_exists = cursor.fetchone()
        if not table_exists:
            print("reading_tasks table does not exist")
            return jsonify({'success': False, 'message': 'Reading tasks not configured. Please contact administrator.'}), 500
        
        # Get appropriate reading tasks for user's class
        cursor.execute("""
            SELECT * FROM reading_tasks 
            WHERE class_level = %s
            ORDER BY difficulty_level, class_level
        """, (class_level,))
        
        tasks = cursor.fetchall()
        print(f"Found {len(tasks)} tasks for class {class_level}")
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': f'No reading tasks found for class {class_level}. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': class_level,
            'total_tasks': len(tasks)
        })
        
    except Exception as e:
        print(f"Get reading tasks error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to fetch reading tasks: {str(e)}'}), 500


def getDefaultReadingTasks():
    """Return default reading tasks when class is not available"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get all available reading tasks
        cursor.execute("SELECT * FROM reading_tasks ORDER BY difficulty_level, class_level")
        tasks = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': 'No reading tasks available. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': 'Not specified',
            'total_tasks': len(tasks),
            'message': 'Showing all available reading tasks. Please update class info for personalized tasks.'
        })
        
    except Exception as e:
        print(f"Get default reading tasks error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch default reading tasks'}), 500


@app.route('/api/reading-task/<int:task_id>', methods=['GET'])
def get_reading_task_by_id(task_id):
    """Get a specific reading task by ID"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get the specific reading task
        cursor.execute("SELECT * FROM reading_tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not task:
            return jsonify({'success': False, 'message': 'Reading task not found'}), 404
        
        return jsonify({
            'success': True, 
            'task': task
        })
        
    except Exception as e:
        print(f"Get reading task by ID error: {e}")
        return jsonify({'success': False, 'message': f'Failed to fetch reading task: {str(e)}'}), 500


@app.route('/api/reading-comprehension-tasks/<int:user_id>', methods=['GET'])
def get_reading_comprehension_tasks(user_id):
    """Get class-appropriate reading comprehension tasks for a user"""
    try:
        print(f"Fetching reading comprehension tasks for user_id: {user_id}")
        
        conn = connect_db()
        if not conn:
            print("Database connection failed")
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # First check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user_exists = cursor.fetchone()
        if not user_exists:
            print(f"User {user_id} not found")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Determine user's class level
        class_level = _get_user_class_level(conn, user_id)
        if not class_level:
            print("No class level; returning default RC tasks")
            return getDefaultReadingComprehensionTasks()
        
        # Check if reading_comprehension_tasks table exists
        cursor.execute("SHOW TABLES LIKE 'reading_comprehension_tasks'")
        table_exists = cursor.fetchone()
        if not table_exists:
            print("reading_comprehension_tasks table does not exist")
            return jsonify({'success': False, 'message': 'Reading comprehension tasks not configured. Please contact administrator.'}), 500
        
        # Get appropriate reading comprehension tasks for user's class
        cursor.execute("""
            SELECT * FROM reading_comprehension_tasks 
            WHERE class_level = %s
            ORDER BY difficulty_level, class_level
        """, (class_level,))
        
        tasks = cursor.fetchall()
        print(f"Found {len(tasks)} comprehension tasks for class {class_level}")
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': f'No reading comprehension tasks found for class {class_level}. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': class_level,
            'total_tasks': len(tasks)
        })
        
    except Exception as e:
        print(f"Get reading comprehension tasks error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to fetch reading comprehension tasks: {str(e)}'}), 500


def getDefaultReadingComprehensionTasks():
    """Return default reading comprehension tasks when class is not available"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get all available reading comprehension tasks
        cursor.execute("SELECT * FROM reading_comprehension_tasks ORDER BY difficulty_level, class_level")
        tasks = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': 'No reading comprehension tasks available. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': 'Not specified',
            'total_tasks': len(tasks),
            'message': 'Showing all available reading comprehension tasks. Please update class info for personalized tasks.'
        })
        
    except Exception as e:
        print(f"Get default reading comprehension tasks error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch default reading comprehension tasks'}), 500


@app.route('/api/reading-comprehension-task/<int:task_id>', methods=['GET'])
def get_reading_comprehension_task_by_id(task_id):
    """Get a specific reading comprehension task by ID"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get the specific reading comprehension task
        cursor.execute("SELECT * FROM reading_comprehension_tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not task:
            return jsonify({'success': False, 'message': 'Reading comprehension task not found'}), 404
        
        return jsonify({
            'success': True, 
            'task': task
        })
        
    except Exception as e:
        print(f"Get reading comprehension task by ID error: {e}")
        return jsonify({'success': False, 'message': f'Failed to fetch reading comprehension task: {str(e)}'}), 500


@app.route('/api/typing-tasks/<int:user_id>', methods=['GET'])
def get_typing_tasks(user_id):
    """Get class-appropriate typing tasks for a user"""
    try:
        print(f"Fetching typing tasks for user_id: {user_id}")
        
        conn = connect_db()
        if not conn:
            print("Database connection failed")
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # First check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user_exists = cursor.fetchone()
        if not user_exists:
            print(f"User {user_id} not found")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Determine user's class level
        class_level = _get_user_class_level(conn, user_id)
        if not class_level:
            print("No class level; returning default typing tasks")
            return getDefaultTypingTasks()
        
        # Check if typing_tasks table exists
        cursor.execute("SHOW TABLES LIKE 'typing_tasks'")
        table_exists = cursor.fetchone()
        if not table_exists:
            print("typing_tasks table does not exist")
            return jsonify({'success': False, 'message': 'Typing tasks not configured. Please contact administrator.'}), 500
        
        # Get appropriate typing tasks for user's class
        cursor.execute("""
            SELECT * FROM typing_tasks 
            WHERE class_level = %s
            ORDER BY difficulty_level, class_level
        """, (class_level,))
        
        tasks = cursor.fetchall()
        print(f"Found {len(tasks)} typing tasks for class {class_level}")
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': f'No typing tasks found for class {class_level}. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': class_level,
            'total_tasks': len(tasks)
        })
        
    except Exception as e:
        print(f"Get typing tasks error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to fetch typing tasks: {str(e)}'}), 500


def getDefaultTypingTasks():
    """Return default typing tasks when class is not available"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get all available typing tasks
        cursor.execute("SELECT * FROM typing_tasks ORDER BY difficulty_level, class_level")
        tasks = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': 'No typing tasks available. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': 'Not specified',
            'total_tasks': len(tasks),
            'message': 'Showing all available typing tasks. Please update class info for personalized tasks.'
        })
        
    except Exception as e:
        print(f"Get default typing tasks error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch default typing tasks'}), 500


@app.route('/api/typing-task/<int:task_id>', methods=['GET'])
def get_typing_task_by_id(task_id):
    """Get a specific typing task by ID"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get the specific typing task
        cursor.execute("SELECT * FROM typing_tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not task:
            return jsonify({'success': False, 'message': 'Typing task not found'}), 404
        
        return jsonify({
            'success': True, 
            'task': task
        })
        
    except Exception as e:
        print(f"Get typing task by ID error: {e}")
        return jsonify({'success': False, 'message': f'Failed to fetch typing task: {str(e)}'}), 500


@app.route('/api/start-typing-task', methods=['POST'])
def start_typing_task():
    """Mark a typing task as started"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_id = data.get('task_id')
    task_name = data.get('task_name')
    
    if not task_id or not task_name:
        return jsonify({'success': False, 'message': 'Task information required'}), 400
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Mark task as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], f'Typing Task {task_name}', 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Task started successfully'})
        
    except Exception as e:
        print(f"Start typing task error: {e}")
        return jsonify({'success': False, 'message': 'Failed to start task'}), 500


@app.route('/api/start-reading-comprehension-task', methods=['POST'])
def start_reading_comprehension_task():
    """Mark a reading comprehension task as started"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_id = data.get('task_id')
    task_name = data.get('task_name')
    
    if not task_id or not task_name:
        return jsonify({'success': False, 'message': 'Task information required'}), 400
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Mark task as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], f'Reading Comprehension Task {task_name}', 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Task started successfully'})
        
    except Exception as e:
        print(f"Start reading comprehension task error: {e}")
        return jsonify({'success': False, 'message': 'Failed to start task'}), 500


@app.route('/api/start-reading-task', methods=['POST'])
def start_reading_task():
    """Mark a reading task as started"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_id = data.get('task_id')
    task_name = data.get('task_name')
    
    if not task_id or not task_name:
        return jsonify({'success': False, 'message': 'Task information required'}), 400
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Mark task as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], f'Reading Task {task_name}', 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Task started successfully'})
        
    except Exception as e:
        print(f"Start reading task error: {e}")
        return jsonify({'success': False, 'message': 'Failed to start task'}), 500


@app.route('/api/mathematical-comprehension-tasks/<int:user_id>', methods=['GET'])
def get_mathematical_comprehension_tasks(user_id):
    """Get class-appropriate mathematical comprehension tasks for a user"""
    try:
        print(f"Fetching mathematical comprehension tasks for user_id: {user_id}")
        
        conn = connect_db()
        if not conn:
            print("Database connection failed")
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # First check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user_exists = cursor.fetchone()
        if not user_exists:
            print(f"User {user_id} not found")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Determine user's class level
        class_level = _get_user_class_level(conn, user_id)
        if not class_level:
            print("No class level; returning default math comp tasks")
            return getDefaultMathematicalComprehensionTasks()
        
        # Check if mathematical_comprehension_tasks table exists
        cursor.execute("SHOW TABLES LIKE 'mathematical_comprehension_tasks'")
        table_exists = cursor.fetchone()
        if not table_exists:
            print("mathematical_comprehension_tasks table does not exist")
            return jsonify({'success': False, 'message': 'Mathematical comprehension tasks not configured. Please contact administrator.'}), 500
        
        # Get appropriate mathematical comprehension tasks for user's class
        cursor.execute("""
            SELECT * FROM mathematical_comprehension_tasks 
            WHERE class_level = %s
            ORDER BY difficulty_level, class_level
        """, (class_level,))
        
        tasks = cursor.fetchall()
        print(f"Found {len(tasks)} mathematical comprehension tasks for class {class_level}")
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': f'No mathematical comprehension tasks found for class {class_level}. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': class_level,
            'total_tasks': len(tasks)
        })
        
    except Exception as e:
        print(f"Get mathematical comprehension tasks error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to fetch mathematical comprehension tasks: {str(e)}'}), 500


def getDefaultMathematicalComprehensionTasks():
    """Return default mathematical comprehension tasks when class is not available"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get all available mathematical comprehension tasks
        cursor.execute("SELECT * FROM mathematical_comprehension_tasks ORDER BY difficulty_level, class_level")
        tasks = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': 'No mathematical comprehension tasks available. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': 'Not specified',
            'total_tasks': len(tasks),
            'message': 'Showing all available mathematical comprehension tasks. Please update class info for personalized tasks.'
        })
        
    except Exception as e:
        print(f"Get default mathematical comprehension tasks error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch default mathematical comprehension tasks'}), 500


@app.route('/api/mathematical-comprehension-task/<int:task_id>', methods=['GET'])
def get_mathematical_comprehension_task_by_id(task_id):
    """Get a specific mathematical comprehension task by ID"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get the specific mathematical comprehension task
        cursor.execute("SELECT * FROM mathematical_comprehension_tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not task:
            return jsonify({'success': False, 'message': 'Mathematical comprehension task not found'}), 404
        
        return jsonify({
            'success': True, 
            'task': task
        })
        
    except Exception as e:
        print(f"Get mathematical comprehension task by ID error: {e}")
        return jsonify({'success': False, 'message': f'Failed to fetch mathematical comprehension task: {str(e)}'}), 500


@app.route('/api/start-mathematical-comprehension-task', methods=['POST'])
def start_mathematical_comprehension_task():
    """Mark a mathematical comprehension task as started"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_id = data.get('task_id')
    task_name = data.get('task_name')
    
    if not task_id or not task_name:
        return jsonify({'success': False, 'message': 'Task information required'}), 400
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Mark task as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], f'Mathematical Comprehension', 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Task started successfully'})
        
    except Exception as e:
        print(f"Start mathematical comprehension task error: {e}")
        return jsonify({'success': False, 'message': 'Failed to start task'}), 500

@app.route('/api/writing-tasks/<int:user_id>', methods=['GET'])
def get_writing_tasks(user_id):
    """Get class-appropriate writing tasks for a user"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Determine user's class level
        class_level = _get_user_class_level(conn, user_id)
        if not class_level:
            return getDefaultWritingTasks()
        
        # Get writing tasks for class
        cursor.execute("""
            SELECT * FROM writing_tasks 
            WHERE class_level = %s
            ORDER BY difficulty_level, class_level
        """, (class_level,))
        tasks = cursor.fetchall()
        if tasks:
            return jsonify({
                'success': True,
                'tasks': tasks,
                'class_level': class_level,
                'message': f'Showing writing tasks for class {class_level}'
            })
        else:
            return getDefaultWritingTasks()
            
    except Exception as e:
        print(f"Get writing tasks error: {e}")
        return jsonify({'success': False, 'message': 'Failed to load writing tasks'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def getDefaultWritingTasks():
    """Get default writing tasks when class is not available"""
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get all writing tasks ordered by difficulty
        cursor.execute("""
            SELECT * FROM writing_tasks 
            ORDER BY difficulty_level, class_level
        """)
        tasks = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'class_level': 'Not specified',
            'message': 'Showing all available writing tasks'
        })
        
    except Exception as e:
        print(f"Get default writing tasks error: {e}")
        return jsonify({'success': False, 'message': 'Failed to load writing tasks'}), 500

@app.route('/api/writing-task/<int:task_id>', methods=['GET'])
def get_writing_task_by_id(task_id):
    """Get a specific writing task by ID"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get the specific writing task
        cursor.execute("SELECT * FROM writing_tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not task:
            return jsonify({'success': False, 'message': 'Writing task not found'}), 404
        
        return jsonify({
            'success': True, 
            'task': task
        })
        
    except Exception as e:
        print(f"Get writing task by ID error: {e}")
        return jsonify({'success': False, 'message': 'Failed to load writing task'}), 500

@app.route('/api/start-writing-task', methods=['POST'])
def start_writing_task():
    """Mark a writing task as started"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_id = data.get('task_id')
    task_name = data.get('task_name')
    
    if not task_id or not task_name:
        return jsonify({'success': False, 'message': 'Task information required'}), 400
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Mark task as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], f'Writing Task {task_name}', 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Task started successfully'})
        
    except Exception as e:
        print(f"Start writing task DB error: {e}")
        return jsonify({'success': False, 'message': 'Failed to start task'}), 500

@app.route('/api/aptitude-tasks/<int:user_id>', methods=['GET'])
def get_aptitude_tasks(user_id):
    """Get class-appropriate aptitude tasks for a user"""
    try:
        print(f"Fetching aptitude tasks for user_id: {user_id}")
        
        conn = connect_db()
        if not conn:
            print("Database connection failed")
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # First check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user_exists = cursor.fetchone()
        if not user_exists:
            print(f"User {user_id} not found")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Determine user's class level
        class_level = _get_user_class_level(conn, user_id)
        if not class_level:
            return getDefaultAptitudeTasks()
        
        # Check if aptitude_tasks table exists
        cursor.execute("SHOW TABLES LIKE 'aptitude_tasks'")
        table_exists = cursor.fetchone()
        if not table_exists:
            print("aptitude_tasks table does not exist")
            return jsonify({'success': False, 'message': 'Aptitude tasks not configured. Please contact administrator.'}), 500
        
        # Get appropriate aptitude tasks for user's class
        cursor.execute("""
            SELECT * FROM aptitude_tasks 
            WHERE class_level = %s 
            ORDER BY difficulty_level, class_level
        """, (class_level,))
        
        tasks = cursor.fetchall()
        print(f"Found {len(tasks)} aptitude tasks for class {class_level}")
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': f'No aptitude tasks found for class {class_level}. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': class_level,
            'total_tasks': len(tasks)
        })
        
    except Exception as e:
        print(f"Get aptitude tasks error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to fetch aptitude tasks: {str(e)}'}), 500


def getDefaultAptitudeTasks():
    """Return default aptitude tasks when class is not available"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get all available aptitude tasks
        cursor.execute("SELECT * FROM aptitude_tasks ORDER BY difficulty_level, class_level")
        tasks = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not tasks:
            return jsonify({'success': False, 'message': 'No aptitude tasks available. Please contact administrator.'}), 404
        
        return jsonify({
            'success': True, 
            'tasks': tasks, 
            'class_level': 'Not specified',
            'total_tasks': len(tasks),
            'message': 'Showing all available aptitude tasks. Please update class info for personalized tasks.'
        })
        
    except Exception as e:
        print(f"Get default aptitude tasks error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch default aptitude tasks'}), 500


@app.route('/api/aptitude-task/<int:task_id>', methods=['GET'])
def get_aptitude_task_by_id(task_id):
    """Get a specific aptitude task by ID"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get the specific aptitude task
        cursor.execute("SELECT * FROM aptitude_tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not task:
            return jsonify({'success': False, 'message': 'Aptitude task not found'}), 404
        
        return jsonify({
            'success': True, 
            'task': task
        })
        
    except Exception as e:
        print(f"Get aptitude task by ID error: {e}")
        return jsonify({'success': False, 'message': f'Failed to fetch aptitude task: {str(e)}'}), 500


@app.route('/api/start-aptitude-task', methods=['POST'])
def start_aptitude_task():
    """Mark an aptitude task as started"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_id = data.get('task_id')
    task_name = data.get('task_name')
    
    if not task_id or not task_name:
        return jsonify({'success': False, 'message': 'Task information required'}), 400
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Mark task as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], f'Aptitude Test {task_name}', 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Task started successfully'})
        
    except Exception as e:
        print(f"Start aptitude task error: {e}")
        return jsonify({'success': False, 'message': 'Failed to start task'}), 500

@app.route('/api/upload-writing', methods=['POST'])
def upload_writing():
    """Upload writing sample image"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    if 'writing_image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file provided'}), 400
    
    file = request.files['writing_image']
    task_id = request.form.get('task_id')
    task_name = request.form.get('task_name', 'Writing Task')
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if not task_id:
        return jsonify({'success': False, 'message': 'Task ID required'}), 400
    
    # Check if file is an image
    if file and allowed_file(file.filename):
        filename = secure_filename(f"writing_user{session['user_id']}_task{task_id}_" + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            
            # Get or create task attempt
            cursor.execute("""
                SELECT id, attempt_number FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
                ORDER BY attempt_number DESC LIMIT 1
            """, (session['user_id'], task_id))
            
            attempt_row = cursor.fetchone()
            if attempt_row:
                attempt_id = attempt_row['id']
                attempt_number = attempt_row['attempt_number']
            else:
                # Create new attempt
                cursor.execute("""
                    SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt
                    FROM user_task_attempts 
                    WHERE user_id = %s AND task_id = %s
                """, (session['user_id'], task_id))
                next_attempt = cursor.fetchone()['next_attempt']
                
                cursor.execute("""
                    INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                    VALUES (%s, %s, %s, 'In Progress', NOW())
                """, (session['user_id'], task_id, next_attempt))
                attempt_id = cursor.lastrowid
                attempt_number = next_attempt
            
            # Save writing sample to database as completed
            cursor.execute("""
                INSERT INTO writing_samples (attempt_id, filename, status, uploaded_at)
                VALUES (%s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE filename = VALUES(filename), status = VALUES(status), uploaded_at = NOW()
            """, (attempt_id, filename, 'Completed'))
            
            # Mark attempt as completed
            cursor.execute("""
                UPDATE user_task_attempts 
                SET status = 'Completed', completed_at = NOW()
                WHERE id = %s
            """, (attempt_id,))
            
            # Mark user_tasks as Completed
            cursor.execute("""
                INSERT INTO user_tasks (user_id, task_name, status)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
            """, (session['user_id'], task_name, 'Completed'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Writing sample uploaded successfully', 'filename': filename, 'attempt_id': attempt_id, 'attempt_number': attempt_number})
            
        except Exception as e:
            print(f"Upload writing DB error: {e}")
            return jsonify({'success': False, 'message': 'Failed to save writing sample'}), 500
    else:
        return jsonify({'success': False, 'message': 'Invalid file type. Please upload an image.'}), 400

@app.route('/api/save-writing-progress', methods=['POST'])
def save_writing_progress():
    """Save writing task progress without marking as completed"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    if 'writing_image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file provided'}), 400
    
    file = request.files['writing_image']
    task_id = request.form.get('task_id')
    task_name = request.form.get('task_name', 'Writing Task')
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if not task_id:
        return jsonify({'success': False, 'message': 'Task ID required'}), 400
    
    # Check if file is an image
    if file and allowed_file(file.filename):
        filename = secure_filename(f"writing_user{session['user_id']}_task{task_id}_" + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            
            # Get or create task attempt
            cursor.execute("""
                SELECT id, attempt_number FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
                ORDER BY attempt_number DESC LIMIT 1
            """, (session['user_id'], task_id))
            
            attempt_row = cursor.fetchone()
            if attempt_row:
                attempt_id = attempt_row['id']
                attempt_number = attempt_row['attempt_number']
            else:
                # Create new attempt
                cursor.execute("""
                    SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt
                    FROM user_task_attempts 
                    WHERE user_id = %s AND task_id = %s
                """, (session['user_id'], task_id))
                next_attempt = cursor.fetchone()['next_attempt']
                
                cursor.execute("""
                    INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                    VALUES (%s, %s, %s, 'In Progress', NOW())
                """, (session['user_id'], task_id, next_attempt))
                attempt_id = cursor.lastrowid
                attempt_number = next_attempt
            
            # Save writing sample to database with In Progress status
            cursor.execute("""
                INSERT INTO writing_samples (attempt_id, filename, status, uploaded_at)
                VALUES (%s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE filename = VALUES(filename), uploaded_at = NOW()
            """, (attempt_id, filename, 'In Progress'))
            
            # Mark user_tasks as In Progress
            cursor.execute("""
                INSERT INTO user_tasks (user_id, task_name, status)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
            """, (session['user_id'], task_name, 'In Progress'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Writing progress saved successfully', 'filename': filename, 'attempt_id': attempt_id, 'attempt_number': attempt_number})
            
        except Exception as e:
            print(f"Save writing progress DB error: {e}")
            return jsonify({'success': False, 'message': 'Failed to save writing progress'}), 500
    else:
        return jsonify({'success': False, 'message': 'Invalid file type. Please upload an image.'}), 400


@app.route('/api/admin/tasks', methods=['GET'])
def get_all_tasks():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM tasks ORDER BY id')
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"Found {len(tasks)} tasks in database")
        for task in tasks:
            print(f"Task: {task}")
        
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        print(f"Error in get_all_tasks: {e}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

# @app.route('/api/admin/tasks', methods=['POST'])
# def add_task():
#     if not session.get('is_admin'):
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#     data = request.get_json()
#     task_name = data.get('task_name')
#     description = data.get('description', '')
#     instructions = data.get('instructions', '')
#     estimated_time = data.get('estimated_time', '')
#     devices_required = data.get('devices_required', '')
#     example = data.get('example', '')
#     if not task_name or not description or not instructions or not estimated_time or not devices_required or not example:
#         return jsonify({'success': False, 'message': 'All fields are required'}), 400
#     conn = connect_db()
#     cursor = conn.cursor()
#     try:
#         cursor.execute('''
#             INSERT INTO tasks (task_name, description, instructions, estimated_time, devices_required, example)
#             VALUES (%s, %s, %s, %s, %s, %s)
#         ''', (task_name, description, instructions, estimated_time, devices_required, example))
#         conn.commit()
#         # Optionally: create the HTML file for the task here (see below)
#         return jsonify({'success': True, 'message': 'Task added'})
#     except Exception as e:
#         conn.rollback()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         cursor.close()
#         conn.close()

@app.route('/api/admin/tasks', methods=['POST'])
def add_task():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    data = request.get_json()
    task_name = data.get('task_name')
    description = data.get('description', '')
    instructions = data.get('instructions', '')
    estimated_time = data.get('estimated_time', '')
    devices_required = data.get('devices_required', '')
    example = data.get('example', '')
    main_content = data.get('main_content', '')
    if not task_name or not description or not instructions or not estimated_time or not devices_required or not example:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO tasks (task_name, description, instructions, estimated_time, devices_required, example)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (task_name, description, instructions, estimated_time, devices_required, example))
        conn.commit()
        # Create the HTML file for the task
        create_task_html(task_name, instructions, estimated_time, devices_required, example, main_content)
        return jsonify({'success': True, 'message': 'Task added'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/tasks/<int:task_id>', methods=['PUT'])
def edit_task(task_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    data = request.get_json()
    task_name = data.get('task_name')
    description = data.get('description', '')
    if not task_name:
        return jsonify({'success': False, 'message': 'Task name required'}), 400
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE tasks SET task_name = %s, description = %s WHERE id = %s', (task_name, description, task_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Task updated'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Get the task name before deleting (for tables using task_name)
        cursor.execute('SELECT task_name FROM tasks WHERE id = %s', (task_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        task_name = row[0]

        # Delete from user_tasks
        cursor.execute('DELETE FROM user_tasks WHERE task_name = %s', (task_name,))
        # Delete from audio_recordings (if task_name is used)
        cursor.execute('DELETE FROM audio_recordings WHERE task_name = %s', (task_name,))
        # Add more deletes here if other tables reference task_name or task_id

        # Finally, delete from tasks table
        cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Task deleted'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/users', methods=['GET'])
def admin_users_list():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = connect_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Join users and demographics
        cursor.execute('''
            SELECT u.id, u.name, u.email, d.age, d.gender, d.dyslexia_status, d.education_level, d.native_language, u.created_at
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
        ''')
        users = cursor.fetchall()
        # Define the set of all tasks
        all_tasks = ['Reading Aloud Task 1', 'Typing Task', 'Reading Comprehension', 'Mathematical Comprehension','Writing Task','Aptitude Test']
        total_tasks = len(all_tasks)
        for user in users:
            # Get completed tasks for this user (only those in all_tasks)
            cursor.execute("""
                SELECT task_name FROM user_tasks WHERE user_id = %s AND status = 'Completed'
            """, (user['id'],))
            completed_tasks = [row['task_name'] for row in cursor.fetchall() if row['task_name'] in all_tasks]
            user['progress'] = int((len(completed_tasks) / total_tasks) * 100) if total_tasks else 0
            user['dyslexia_status'] = user.get('dyslexia_status', 'N/A')
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({'success': False, 'message': 'Error fetching users'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
def admin_user_detail(user_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = connect_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Join users and demographics for full details
        cursor.execute('''
            SELECT u.id, u.name, u.email, d.age, d.gender, d.dyslexia_status, d.education_level, d.native_language, u.created_at
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
            WHERE u.id = %s
        ''', (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        # Fetch user task progress
        cursor.execute('SELECT task_name, status FROM user_tasks WHERE user_id = %s', (user_id,))
        tasks = cursor.fetchall()
        user['tasks'] = tasks
        return jsonify({'success': True, 'user': user})
    except Exception as e:
        print(f"Error fetching user detail: {e}")
        return jsonify({'success': False, 'message': 'Error fetching user detail'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/users-grouped', methods=['GET'])
def admin_users_grouped():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = connect_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Parents
        cursor.execute('''
            SELECT u.id, u.name, u.email, u.created_at
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
            WHERE u.user_type = 'parent'
        ''')
        parents = cursor.fetchall()

        # Children (with school/class/section labels)
        cursor.execute('''
            SELECT u.id, u.name, u.email, d.age, d.gender, d.dyslexia_status, d.education_level, d.native_language, u.created_at,
                   scls.name AS school_name, cls.name AS class_name, sec.name AS section_name
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
            LEFT JOIN class_sections sec ON sec.id = u.section_id
            LEFT JOIN school_classes cls ON cls.id = sec.class_id
            LEFT JOIN schools scls ON scls.id = u.school_id
            WHERE u.user_type = 'child'
        ''')
        children = cursor.fetchall()

        # Schools
        cursor.execute('''
            SELECT s.id, s.name, s.email, s.address, s.phone, s.created_at
            FROM schools s
            ORDER BY s.created_at DESC
        ''')
        schools = cursor.fetchall()

        # Compute progress for parents and children
        all_tasks = ['Reading Aloud Task 1', 'Typing Task', 'Reading Comprehension', 'Mathematical Comprehension','Writing Task','Aptitude Test']
        total_tasks = len(all_tasks)
        def attach_progress(users):
            for u in users:
                cursor.execute("""
                    SELECT task_name FROM user_tasks WHERE user_id = %s AND status = 'Completed'
                """, (u['id'],))
                completed = [row['task_name'] for row in cursor.fetchall() if row['task_name'] in all_tasks]
                u['progress'] = int((len(completed) / total_tasks) * 100) if total_tasks else 0
                u['dyslexia_status'] = u.get('dyslexia_status', 'N/A')
        attach_progress(parents)
        attach_progress(children)

        # Attach counts to schools
        for s in schools:
            # number of parents in this school
            cursor.execute("SELECT COUNT(*) AS c FROM users WHERE user_type = 'parent' AND school_id = %s", (s['id'],))
            s['num_parents'] = cursor.fetchone()['c']
            # number of children linked to those parents
            cursor.execute('''
                SELECT COUNT(DISTINCT pc.child_id) AS c
                FROM parent_children pc
                JOIN users p ON p.id = pc.parent_id
                WHERE p.school_id = %s
            ''', (s['id'],))
            s['num_children'] = cursor.fetchone()['c']

            core_tasks = ['Reading Aloud Task 1', 'Typing Task', 'Reading Comprehension', 'Mathematical Comprehension', 'Writing Task', 'Aptitude Test']
            cursor.execute('''
                SELECT u.id
                FROM users u
                WHERE u.user_type = 'child' AND u.parent_id IN (
                    SELECT id FROM users WHERE user_type = 'parent' AND school_id = %s
                )
            ''', (s['id'],))
            child_ids = [row['id'] for row in cursor.fetchall()]
            assessments_completed = 0
            for child_id in child_ids:
                cursor.execute('''
                    SELECT task_name, status FROM user_tasks WHERE user_id = %s
                ''', (child_id,))
                statuses = {row['task_name']: row['status'] for row in cursor.fetchall()}
                if all(statuses.get(t) == 'Completed' for t in core_tasks):
                    assessments_completed += 1
            s['assessments_completed'] = assessments_completed

        # Build hierarchy: School -> Class -> Section -> Parent -> Student; plus unassigned
        hierarchy = []
        cursor.execute("SELECT id, name FROM schools ORDER BY name")
        for school in cursor.fetchall():
            school_entry = {'id': school['id'], 'name': school['name'], 'classes': []}
            cursor.execute("SELECT id, name FROM school_classes WHERE school_id = %s ORDER BY name", (school['id'],))
            for cls in cursor.fetchall():
                class_entry = {'id': cls['id'], 'name': cls['name'], 'sections': []}
                cursor.execute("SELECT id, name FROM class_sections WHERE class_id = %s ORDER BY name", (cls['id'],))
                for sec in cursor.fetchall():
                    section_entry = {'id': sec['id'], 'name': sec['name'], 'parents': [], 'students': []}
                    cursor.execute("SELECT id, name, email FROM users WHERE user_type='parent' AND section_id=%s ORDER BY name", (sec['id'],))
                    section_entry['parents'] = cursor.fetchall()
                    cursor.execute("SELECT id, name, email FROM users WHERE user_type='child' AND section_id=%s ORDER BY name", (sec['id'],))
                    section_entry['students'] = cursor.fetchall()
                    class_entry['sections'].append(section_entry)
                school_entry['classes'].append(class_entry)
            hierarchy.append(school_entry)

        cursor.execute("SELECT id, name, email FROM users WHERE user_type='parent' AND school_id IS NULL ORDER BY name")
        unassigned_parents = cursor.fetchall()
        for p in unassigned_parents:
            cursor.execute("SELECT id, name, email FROM users WHERE user_type='child' AND (parent_id=%s OR id IN (SELECT child_id FROM parent_children WHERE parent_id=%s)) AND school_id IS NULL ORDER BY name", (p['id'], p['id']))
            p['children'] = cursor.fetchall()

        combined_users=(parents or []) + (children or [])
        return jsonify({'success':True, 'parents':parents, 'children': children, 'schools': schools, 'users': combined_users, 'hierarchy': hierarchy, 'unassigned': {'parents': unassigned_parents}})
    except Exception as e:
        print(f"Error fetching grouped users: {e}")
        return jsonify({'success': False, 'message': 'Error fetching grouped users'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/suggested-tasks', methods=['GET'])
def admin_list_suggested_tasks():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = connect_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            '''
            SELECT st.id, st.task_name, st.category, st.description, st.estimated_time, st.devices_required, st.details,
                   st.status, st.created_at, s.name AS school_name, s.email AS school_email
            FROM suggested_tasks st
            JOIN schools s ON s.id = st.school_id
            ORDER BY st.created_at DESC
            '''
        )
        rows = cur.fetchall()
        return jsonify({'success': True, 'suggestions': rows})
    except Exception as e:
        print(f"Error fetching suggested tasks: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch suggestions'}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/users/<int:user_id>/export', methods=['GET'])
def admin_user_export(user_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = connect_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, name, email, age, gender, dyslexia_status, education_level, native_language, created_at, status
            FROM users WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        cursor.execute("""
            SELECT task_name, status FROM user_tasks WHERE user_id = %s
        """, (user_id,))
        tasks = cursor.fetchall()
        user['tasks'] = tasks
        import json
        from flask import make_response
        response = make_response(json.dumps(user, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=user_{user_id}_data.json'
        return response
    except Exception as e:
        print(f"Error exporting user data: {e}")
        return jsonify({'success': False, 'message': 'Error exporting user data'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/dashboard-stats', methods=['GET'])
def admin_dashboard_stats():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = connect_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    stats = {}  # <-- Initialize stats dictionary
    try:
        # Total participants
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE user_type = 'child'")
        total_participants = cursor.fetchone()['total']
        stats['totalParticipants'] = total_participants

        # Average completion rate (average progress across all users)
        cursor.execute('SELECT id FROM users')
        user_ids = [row['id'] for row in cursor.fetchall()]
        total_progress = 0
        for user_id in user_ids:
            cursor.execute('SELECT COUNT(*) as total FROM user_tasks WHERE user_id = %s', (user_id,))
            total_tasks = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as completed FROM user_tasks WHERE user_id = %s AND status = 'Completed'", (user_id,))
            completed_tasks = cursor.fetchone()['completed']
            progress = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
            total_progress += progress
        avg_completion = int(total_progress / len(user_ids)) if user_ids else 0
        stats['completionRate'] = avg_completion

        # Active studies (number of tasks)
        cursor.execute('SELECT COUNT(*) AS numTasks FROM tasks')
        stats['activeStudies'] = cursor.fetchone()['numTasks']

        # Data quality calculation based on demographics completion
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT u.id) as total_students,
                COUNT(DISTINCT d.user_id) as students_with_demographics
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
            WHERE u.user_type = 'child'
        ''')
        data_quality_result = cursor.fetchone()
        data_quality = 0
        if data_quality_result['total_students'] > 0:
            data_quality = round((data_quality_result['students_with_demographics'] / data_quality_result['total_students']) * 100, 1)
        stats['dataQuality'] = data_quality

        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        return jsonify({'success': False, 'message': 'Error fetching dashboard stats'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/get-child-tasks', methods=['GET'])
def admin_get_child_tasks():
    """Get all tasks for a specific child user"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'}), 400
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get all available tasks
        cursor.execute("SELECT task_name FROM tasks ORDER BY id")
        all_tasks = [row['task_name'] for row in cursor.fetchall()]
        
        # Get current task statuses for this user
        cursor.execute("SELECT task_name, status FROM user_tasks WHERE user_id = %s", (user_id,))
        user_tasks = {row['task_name']: row['status'] for row in cursor.fetchall()}
        
        # Create task list with current status or 'Not Started' as default
        tasks = []
        for task_name in all_tasks:
            status = user_tasks.get(task_name, 'Not Started')
            tasks.append({'task_name': task_name, 'status': status})
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'tasks': tasks})
        
    except Exception as e:
        print(f"Error getting child tasks: {e}")
        return jsonify({'success': False, 'message': f'Failed to get tasks: {str(e)}'}), 500




@app.route('/api/get-writing-progress', methods=['GET'])
def get_writing_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    task_name = request.args.get('task_name', 'Writing Task')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get the latest IN PROGRESS attempt and its progress (not completed ones)
        # Order by progress uploaded_at to get the most recent saved progress
        cursor.execute('''
            SELECT 
                uta.id as attempt_id,
                uta.attempt_number,
                uta.status as attempt_status,
                uta.started_at,
                uta.completed_at,
                ws.filename, ws.status as progress_status, ws.uploaded_at
            FROM user_task_attempts uta
            LEFT JOIN writing_samples ws ON ws.attempt_id = uta.id
            WHERE uta.user_id = %s AND uta.task_id = %s AND uta.status = 'In Progress'
            ORDER BY ws.uploaded_at DESC
            LIMIT 1
        ''', (session['user_id'], task_id))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                'success': True, 
                'progress': {
                    'filename': result.get('filename', ''),
                    'status': result.get('progress_status', 'In Progress'),
                    'attempt_id': result.get('attempt_id'),
                    'attempt_number': result.get('attempt_number'),
                    'attempt_status': result.get('attempt_status'),
                    'started_at': result.get('started_at'),
                    'completed_at': result.get('completed_at'),
                    'uploaded_at': result.get('uploaded_at')
                }
            })
        else:
            return jsonify({'success': True, 'progress': None})
    except Exception as e:
        print(f"Get writing progress error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get writing progress'}), 500


@app.route('/api/admin/set-user-task-status', methods=['POST'])
def admin_set_user_task_status():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    data = request.get_json()
    user_id = data.get('user_id')
    task_name = data.get('task_name')
    status = data.get('status')
    if not user_id or not task_name or not status:
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (user_id, task_name, status))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# app.py
from flask import request, jsonify
import smtplib
from email.message import EmailMessage

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    # Compose email
    msg = EmailMessage()
    msg['Subject'] = f"Contact Form: {subject}"
    msg['From'] = email
    msg['To'] = 'yourteam@email.com'
    msg.set_content(f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}")

    # Send email (configure SMTP for your provider)
    try:
        with smtplib.SMTP('smtp.yourprovider.com', 587) as server:
            server.starttls()
            server.login('yourteam@email.com', 'yourpassword')
            server.send_message(msg)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/api/admin/data-quality-metrics', methods=['GET'])
def get_data_quality_metrics():
    """Get detailed data quality metrics for admin dashboard."""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # Audio Quality - based on audio recordings completion
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT u.id) as total_students,
                COUNT(DISTINCT ar.user_id) as students_with_audio
            FROM users u
            LEFT JOIN audio_recordings ar ON u.id = ar.user_id
            WHERE u.user_type = 'child'
        ''')
        audio_quality_result = cursor.fetchone()
        audio_quality = 0
        if audio_quality_result['total_students'] > 0:
            audio_quality = round((audio_quality_result['students_with_audio'] / audio_quality_result['total_students']) * 100, 1)

        # Response Completeness - based on task completion rates
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT u.id) as total_students,
                COUNT(DISTINCT CASE WHEN ut.status = 'Completed' THEN u.id END) as students_with_completed_tasks
            FROM users u
            LEFT JOIN user_tasks ut ON u.id = ut.user_id
            WHERE u.user_type = 'child'
        ''')
        response_completeness_result = cursor.fetchone()
        response_completeness = 0
        if response_completeness_result['total_students'] > 0:
            response_completeness = round((response_completeness_result['students_with_completed_tasks'] / response_completeness_result['total_students']) * 100, 1)

        # Data Consistency - based on demographics completeness
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT u.id) as total_students,
                COUNT(DISTINCT d.user_id) as students_with_demographics
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
            WHERE u.user_type = 'child'
        ''')
        data_consistency_result = cursor.fetchone()
        data_consistency = 0
        if data_consistency_result['total_students'] > 0:
            data_consistency = round((data_consistency_result['students_with_demographics'] / data_consistency_result['total_students']) * 100, 1)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'audio_quality': audio_quality,
                'response_completeness': response_completeness,
                'data_consistency': data_consistency
            }
        })

    except Exception as e:
        print(f"Error getting data quality metrics: {e}")
        return jsonify({'success': False, 'message': 'Failed to load data quality metrics'}), 500

# ========== COMPREHENSIVE STATISTICS API ENDPOINTS ==========

@app.route('/api/school/statistics', methods=['GET'])
def get_school_statistics():
    """Get comprehensive statistics for the current school."""
    if 'school_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        school_id = session['school_id']

        # Get school basic info
        cursor.execute('SELECT name, email, phone FROM schools WHERE id = %s', (school_id,))
        school_info = cursor.fetchone()

        # Get total counts
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT CASE WHEN u.user_type = 'parent' THEN u.id END) as total_parents,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' THEN u.id END) as total_students,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' AND u.is_active = 1 THEN u.id END) as active_students
            FROM users u 
            WHERE u.school_id = %s
        ''', (school_id,))
        counts = cursor.fetchone()

        # Get class-wise distribution
        cursor.execute('''
            SELECT 
                u.class,
                COUNT(DISTINCT CASE WHEN u.user_type = 'parent' THEN u.id END) as parents,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' THEN u.id END) as students,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' AND u.is_active = 1 THEN u.id END) as active_students
            FROM users u 
            WHERE u.school_id = %s AND u.class IS NOT NULL
            GROUP BY u.class
            ORDER BY u.class
        ''', (school_id,))
        class_stats = cursor.fetchall()

        # Get task completion statistics
        cursor.execute('''
            SELECT 
                t.task_name,
                COUNT(DISTINCT ut.user_id) as total_attempts,
                COUNT(DISTINCT CASE WHEN ut.status = 'Completed' THEN ut.user_id END) as completed_count,
                ROUND(COUNT(DISTINCT CASE WHEN ut.status = 'Completed' THEN ut.user_id END) * 100.0 / COUNT(DISTINCT ut.user_id), 2) as completion_rate
            FROM tasks t
            LEFT JOIN user_tasks ut ON t.task_name = ut.task_name
            LEFT JOIN users u ON ut.user_id = u.id AND u.school_id = %s AND u.user_type = 'child'
            GROUP BY t.task_name
            ORDER BY t.task_name
        ''', (school_id,))
        task_stats = cursor.fetchall()

        # Get recent activity (last 7 days)
        cursor.execute('''
            SELECT 
                DATE(ut.updated_at) as date,
                COUNT(*) as task_updates,
                COUNT(CASE WHEN ut.status = 'Completed' THEN 1 END) as completions
            FROM user_tasks ut
            JOIN users u ON ut.user_id = u.id
            WHERE u.school_id = %s 
            AND ut.updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(ut.updated_at)
            ORDER BY date DESC
        ''', (school_id,))
        recent_activity = cursor.fetchall()

        # Get demographics breakdown
        cursor.execute('''
            SELECT 
                d.gender,
                d.dyslexia_status,
                COUNT(*) as count
            FROM demographics d
            JOIN users u ON d.user_id = u.id
            WHERE u.school_id = %s AND u.user_type = 'child'
            GROUP BY d.gender, d.dyslexia_status
        ''', (school_id,))
        demographics = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'school_info': school_info,
                'counts': counts,
                'class_stats': class_stats,
                'task_stats': task_stats,
                'recent_activity': recent_activity,
                'demographics': demographics
            }
        })

    except Exception as e:
        print(f"Error getting school statistics: {e}")
        return jsonify({'success': False, 'message': 'Failed to load statistics'}), 500

@app.route('/api/parent/statistics', methods=['GET'])
def get_parent_statistics():
    """Get comprehensive statistics for the current parent's children."""
    if 'user_id' not in session or session.get('user_type') != 'parent':
        return jsonify({'success': False, 'message': 'Not logged in as parent'}), 401

    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        parent_id = session['user_id']

        # Get parent's children
        cursor.execute('''
            SELECT 
                u.id, u.name, u.email, u.class, u.is_active,
                d.age, d.gender, d.dyslexia_status, d.education_level,
                s.name as school_name
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
            LEFT JOIN schools s ON u.school_id = s.id
            WHERE u.parent_id = %s AND u.user_type = 'child'
            ORDER BY u.name
        ''', (parent_id,))
        children = cursor.fetchall()

        # Get detailed statistics for each child
        children_stats = []
        for child in children:
            child_id = child['id']
            
            # Get task progress for this child
            cursor.execute('''
                SELECT 
                    ut.task_name,
                    ut.status,
                    ut.updated_at,
                    CASE 
                        WHEN ut.status = 'Completed' THEN 100
                        WHEN ut.status = 'In Progress' THEN 50
                        ELSE 0
                    END as progress_percentage
                FROM user_tasks ut
                WHERE ut.user_id = %s
                ORDER BY ut.task_name
            ''', (child_id,))
            task_progress = cursor.fetchall()

            # Calculate overall progress
            total_tasks = len(task_progress)
            completed_tasks = len([t for t in task_progress if t['status'] == 'Completed'])
            overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # Get recent activity for this child
            cursor.execute('''
                SELECT 
                    ut.task_name,
                    ut.status,
                    ut.updated_at
                FROM user_tasks ut
                WHERE ut.user_id = %s
                ORDER BY ut.updated_at DESC
                LIMIT 5
            ''', (child_id,))
            recent_activity = cursor.fetchall()

            children_stats.append({
                'child_info': child,
                'task_progress': task_progress,
                'overall_progress': round(overall_progress, 1),
                'recent_activity': recent_activity
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'children_count': len(children),
                'children_stats': children_stats
            }
        })

    except Exception as e:
        print(f"Error getting parent statistics: {e}")
        return jsonify({'success': False, 'message': 'Failed to load statistics'}), 500

@app.route('/api/admin/comprehensive-stats', methods=['GET'])
def get_admin_comprehensive_stats():
    """Get comprehensive system-wide statistics for admin."""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # System overview
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT s.id) as total_schools,
                COUNT(DISTINCT CASE WHEN u.user_type = 'parent' THEN u.id END) as total_parents,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' THEN u.id END) as total_students,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' AND u.is_active = 1 THEN u.id END) as active_students,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' AND u.is_active = 0 THEN u.id END) as inactive_students
            FROM schools s
            LEFT JOIN users u ON s.id = u.school_id
        ''')
        system_overview = cursor.fetchone()

        # School-wise statistics
        cursor.execute('''
            SELECT 
                s.id, s.name, s.email,
                COUNT(DISTINCT CASE WHEN u.user_type = 'parent' THEN u.id END) as parents_count,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' THEN u.id END) as students_count,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' AND u.is_active = 1 THEN u.id END) as active_students_count
            FROM schools s
            LEFT JOIN users u ON s.id = u.school_id
            GROUP BY s.id, s.name, s.email
            ORDER BY students_count DESC
        ''')
        school_stats = cursor.fetchall()

        # Task completion statistics
        cursor.execute('''
            SELECT 
                t.task_name,
                COUNT(DISTINCT ut.user_id) as total_attempts,
                COUNT(DISTINCT CASE WHEN ut.status = 'Completed' THEN ut.user_id END) as completed_count,
                COUNT(DISTINCT CASE WHEN ut.status = 'In Progress' THEN ut.user_id END) as in_progress_count,
                COUNT(DISTINCT CASE WHEN ut.status = 'Not Started' THEN ut.user_id END) as not_started_count,
                ROUND(COUNT(DISTINCT CASE WHEN ut.status = 'Completed' THEN ut.user_id END) * 100.0 / COUNT(DISTINCT ut.user_id), 2) as completion_rate
            FROM tasks t
            LEFT JOIN user_tasks ut ON t.task_name = ut.task_name
            LEFT JOIN users u ON ut.user_id = u.id AND u.user_type = 'child'
            GROUP BY t.task_name
            ORDER BY completion_rate DESC
        ''')
        task_completion_stats = cursor.fetchall()

        # Demographics breakdown
        cursor.execute('''
            SELECT 
                d.gender,
                d.dyslexia_status,
                d.education_level,
                COUNT(*) as count
            FROM demographics d
            JOIN users u ON d.user_id = u.id
            WHERE u.user_type = 'child'
            GROUP BY d.gender, d.dyslexia_status, d.education_level
        ''')
        demographics_stats = cursor.fetchall()

        # Recent activity (last 30 days)
        cursor.execute('''
            SELECT 
                DATE(ut.updated_at) as date,
                COUNT(*) as total_updates,
                COUNT(CASE WHEN ut.status = 'Completed' THEN 1 END) as completions,
                COUNT(CASE WHEN ut.status = 'In Progress' THEN 1 END) as progress_updates
            FROM user_tasks ut
            JOIN users u ON ut.user_id = u.id
            WHERE u.user_type = 'child' 
            AND ut.updated_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(ut.updated_at)
            ORDER BY date DESC
        ''')
        recent_activity = cursor.fetchall()

        # Class-wise distribution
        cursor.execute('''
            SELECT 
                u.class,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' THEN u.id END) as students_count,
                COUNT(DISTINCT CASE WHEN u.user_type = 'parent' THEN u.id END) as parents_count,
                COUNT(DISTINCT CASE WHEN u.user_type = 'child' AND u.is_active = 1 THEN u.id END) as active_students_count
            FROM users u
            WHERE u.class IS NOT NULL
            GROUP BY u.class
            ORDER BY u.class
        ''')
        class_distribution = cursor.fetchall()

        # Data quality metrics
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT u.id) as total_students,
                COUNT(DISTINCT d.user_id) as students_with_demographics,
                COUNT(DISTINCT CASE WHEN ut.user_id IS NOT NULL THEN u.id END) as students_with_tasks,
                ROUND(COUNT(DISTINCT d.user_id) * 100.0 / COUNT(DISTINCT u.id), 2) as demographics_completion_rate,
                ROUND(COUNT(DISTINCT CASE WHEN ut.user_id IS NOT NULL THEN u.id END) * 100.0 / COUNT(DISTINCT u.id), 2) as task_participation_rate
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
            LEFT JOIN user_tasks ut ON u.id = ut.user_id
            WHERE u.user_type = 'child'
        ''')
        data_quality = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'system_overview': system_overview,
                'school_stats': school_stats,
                'task_completion_stats': task_completion_stats,
                'demographics_stats': demographics_stats,
                'recent_activity': recent_activity,
                'class_distribution': class_distribution,
                'data_quality': data_quality
            }
        })

    except Exception as e:
        print(f"Error getting admin comprehensive stats: {e}")
        return jsonify({'success': False, 'message': 'Failed to load statistics'}), 500

@app.route('/api/statistics/child/<int:child_id>', methods=['GET'])
def get_child_detailed_stats(child_id):
    """Get detailed statistics for a specific child."""
    # Check if user has permission to view this child's stats
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session['user_id']
        user_type = session.get('user_type')

        # Check permissions
        if user_type == 'parent':
            # Parent can only view their own children
            cursor.execute('SELECT id FROM users WHERE id = %s AND parent_id = %s', (child_id, user_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        elif user_type == 'child':
            # Child can only view their own stats
            if child_id != user_id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        elif not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        # Get child basic info
        cursor.execute('''
            SELECT 
                u.id, u.name, u.email, u.class, u.is_active, u.created_at,
                d.age, d.gender, d.dyslexia_status, d.education_level, d.native_language,
                s.name as school_name
            FROM users u
            LEFT JOIN demographics d ON u.id = d.user_id
            LEFT JOIN schools s ON u.school_id = s.id
            WHERE u.id = %s AND u.user_type = 'child'
        ''', (child_id,))
        child_info = cursor.fetchone()

        if not child_info:
            return jsonify({'success': False, 'message': 'Child not found'}), 404

        # Get detailed task progress
        cursor.execute('''
            SELECT 
                ut.task_name,
                ut.status,
                ut.updated_at,
                CASE 
                    WHEN ut.status = 'Completed' THEN 100
                    WHEN ut.status = 'In Progress' THEN 50
                    ELSE 0
                END as progress_percentage
            FROM user_tasks ut
            WHERE ut.user_id = %s
            ORDER BY ut.task_name
        ''', (child_id,))
        task_progress = cursor.fetchall()

        # Calculate overall progress
        total_tasks = len(task_progress)
        completed_tasks = len([t for t in task_progress if t['status'] == 'Completed'])
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Get task attempt details
        cursor.execute('''
            SELECT 
                uta.task_id,
                t.task_name,
                uta.attempt_number,
                uta.status,
                uta.started_at,
                uta.completed_at,
                TIMESTAMPDIFF(MINUTE, uta.started_at, uta.completed_at) as duration_minutes
            FROM user_task_attempts uta
            JOIN tasks t ON uta.task_id = t.id
            WHERE uta.user_id = %s
            ORDER BY uta.started_at DESC
        ''', (child_id,))
        task_attempts = cursor.fetchall()

        # Get recent activity
        cursor.execute('''
            SELECT 
                ut.task_name,
                ut.status,
                ut.updated_at,
                'task_update' as activity_type
            FROM user_tasks ut
            WHERE ut.user_id = %s
            UNION ALL
            SELECT 
                t.task_name,
                uta.status,
                uta.started_at as updated_at,
                'task_attempt' as activity_type
            FROM user_task_attempts uta
            JOIN tasks t ON uta.task_id = t.id
            WHERE uta.user_id = %s
            ORDER BY updated_at DESC
            LIMIT 10
        ''', (child_id, child_id))
        recent_activity = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'child_info': child_info,
                'task_progress': task_progress,
                'overall_progress': round(overall_progress, 1),
                'task_attempts': task_attempts,
                'recent_activity': recent_activity
            }
        })

    except Exception as e:
        print(f"Error getting child detailed stats: {e}")
        return jsonify({'success': False, 'message': 'Failed to load statistics'}), 500

@app.route('/admin/logout')
def admin_logout_page():
    session.pop('is_admin', None)
    flash('Admin logged out successfully', 'success')
    return redirect(url_for('landing'))

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    return '', 204  # No content, JS will handle redirect

@app.route('/api/get-task-status', methods=['GET'])
def get_task_status():
    """Get the status of a specific task for the current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    task_name = request.args.get('task_name')
    if not task_name:
        return jsonify({'success': False, 'message': 'Task name required'}), 400
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT status FROM user_tasks WHERE user_id = %s AND task_name = %s"
        cursor.execute(query, (session['user_id'], task_name))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        status = result['status'] if result else 'Not Started'
        return jsonify({'success': True, 'status': status})
        
    except Exception as e:
        print(f"Get task status error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get task status'}), 500

@app.route('/api/save-mathematical-comprehension-progress', methods=['POST'])
def save_mathematical_comprehension_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    q1 = data.get('q1', '')
    q2 = data.get('q2', '')
    q3 = data.get('q3', '')
    task_name = data.get('task_name', 'Mathematical Comprehension')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get or create task attempt
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if attempt_row:
            attempt_id = attempt_row['id']
            attempt_number = attempt_row['attempt_number']
        else:
            # Create new attempt
            cursor.execute("""
                SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt
                FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s
            """, (session['user_id'], task_id))
            next_attempt = cursor.fetchone()['next_attempt']
            
            cursor.execute("""
                INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                VALUES (%s, %s, %s, 'In Progress', NOW())
            """, (session['user_id'], task_id, next_attempt))
            attempt_id = cursor.lastrowid
            attempt_number = next_attempt
        
        # Save progress
        cursor.execute('''
            INSERT INTO mathematical_comprehension_progress (attempt_id, q1, q2, q3, status, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE q1=VALUES(q1), q2=VALUES(q2), q3=VALUES(q3), status=VALUES(status), updated_at=NOW()
        ''', (attempt_id, q1, q2, q3, 'In Progress'))
        
        # Mark user_tasks as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Progress saved successfully', 'attempt_id': attempt_id, 'attempt_number': attempt_number})
    except Exception as e:
        print(f"Save mathematical comprehension progress DB error: {e}")
        return jsonify({'success': False, 'message': 'Failed to save progress'}), 500

@app.route('/api/get-mathematical-comprehension-progress', methods=['GET'])
def get_mathematical_comprehension_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    task_name = request.args.get('task_name', 'Mathematical Comprehension')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get the latest IN PROGRESS attempt and its progress (not completed ones)
        # Order by progress updated_at to get the most recent saved progress
        cursor.execute('''
            SELECT 
                uta.id as attempt_id,
                uta.attempt_number,
                uta.status as attempt_status,
                uta.started_at,
                uta.completed_at,
                mcp.q1, mcp.q2, mcp.q3, mcp.status as progress_status, mcp.updated_at
            FROM user_task_attempts uta
            LEFT JOIN mathematical_comprehension_progress mcp ON mcp.attempt_id = uta.id
            WHERE uta.user_id = %s AND uta.task_id = %s AND uta.status = 'In Progress'
            ORDER BY mcp.updated_at DESC
            LIMIT 1
        ''', (session['user_id'], task_id))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                'success': True, 
                'progress': {
                    'q1': result.get('q1', ''),
                    'q2': result.get('q2', ''),
                    'q3': result.get('q3', ''),
                    'status': result.get('progress_status', 'In Progress'),
                    'attempt_id': result.get('attempt_id'),
                    'attempt_number': result.get('attempt_number'),
                    'attempt_status': result.get('attempt_status'),
                    'started_at': result.get('started_at'),
                    'completed_at': result.get('completed_at')
                }
            })
        else:
            return jsonify({'success': True, 'progress': None})
    except Exception as e:
        print(f"Get mathematical comprehension progress error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get progress'}), 500

@app.route('/api/submit-mathematical-comprehension', methods=['POST'])
def submit_mathematical_comprehension():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    q1 = data.get('q1', '')
    q2 = data.get('q2', '')
    q3 = data.get('q3', '')
    task_name = data.get('task_name', 'Mathematical Comprehension')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get or create task attempt
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if attempt_row:
            attempt_id = attempt_row['id']
            attempt_number = attempt_row['attempt_number']
        else:
            # Create new attempt
            cursor.execute("""
                SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt
                FROM user_task_attempts 
                WHERE user_id = %s AND task_id = %s
            """, (session['user_id'], task_id))
            next_attempt = cursor.fetchone()['next_attempt']
            
            cursor.execute("""
                INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
                VALUES (%s, %s, %s, 'In Progress', NOW())
            """, (session['user_id'], task_id, next_attempt))
            attempt_id = cursor.lastrowid
            attempt_number = next_attempt
        
        # Save progress as completed
        cursor.execute('''
            INSERT INTO mathematical_comprehension_progress (attempt_id, q1, q2, q3, status, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE q1=VALUES(q1), q2=VALUES(q2), q3=VALUES(q3), status=VALUES(status), updated_at=NOW()
        ''', (attempt_id, q1, q2, q3, 'Completed'))
        
        # Mark attempt as completed
        cursor.execute("""
            UPDATE user_task_attempts 
            SET status = 'Completed', completed_at = NOW()
            WHERE id = %s
        """, (attempt_id,))
        
        # Mark user_tasks as Completed
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'Completed'))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Task submitted and marked as completed', 'attempt_id': attempt_id, 'attempt_number': attempt_number})
    except Exception as e:
        print(f"Submit mathematical comprehension DB error: {e}")
        return jsonify({'success': False, 'message': 'Failed to submit task'}), 500

@app.route('/api/retake-mathematical-comprehension', methods=['POST'])
def retake_mathematical_comprehension():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_name = data.get('task_name', 'Mathematical Comprehension')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get next attempt number
        cursor.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt
            FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s
        """, (session['user_id'], task_id))
        next_attempt = cursor.fetchone()['next_attempt']
        
        # Create new attempt
        cursor.execute("""
            INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
            VALUES (%s, %s, %s, 'In Progress', NOW())
        """, (session['user_id'], task_id, next_attempt))
        attempt_id = cursor.lastrowid
        
        # Mark user_tasks as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'New attempt created for retake. Previous submissions preserved.',
            'attempt_id': attempt_id,
            'attempt_number': next_attempt,
            'task_name': task_name
        })
    except Exception as e:
        print(f"Error creating retake attempt: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/retake-writing', methods=['POST'])
def retake_writing():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_name = data.get('task_name', 'Writing Task')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get next attempt number
        cursor.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt
            FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s
        """, (session['user_id'], task_id))
        next_attempt = cursor.fetchone()['next_attempt']
        
        # Create new attempt
        cursor.execute("""
            INSERT INTO user_task_attempts (user_id, task_id, attempt_number, status, started_at)
            VALUES (%s, %s, %s, 'In Progress', NOW())
        """, (session['user_id'], task_id, next_attempt))
        attempt_id = cursor.lastrowid
        
        # Mark user_tasks as In Progress
        cursor.execute('''
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'New attempt created for retake. Previous submissions preserved.',
            'attempt_id': attempt_id,
            'attempt_number': next_attempt,
            'task_name': task_name
        })
    except Exception as e:
        print(f"Error creating retake attempt: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/submit-saved-writing', methods=['POST'])
def submit_saved_writing():
    """Submit saved writing progress without uploading a new file"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_name = data.get('task_name', 'Writing Task')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get the latest IN PROGRESS attempt
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if not attempt_row:
            return jsonify({'success': False, 'message': 'No saved progress found'}), 404
        
        attempt_id = attempt_row['id']
        attempt_number = attempt_row['attempt_number']
        
        # Update the writing sample status to completed
        cursor.execute("""
            UPDATE writing_samples 
            SET status = 'Completed', uploaded_at = NOW()
            WHERE attempt_id = %s
        """, (attempt_id,))
        
        # Mark attempt as completed
        cursor.execute("""
            UPDATE user_task_attempts 
            SET status = 'Completed', completed_at = NOW()
            WHERE id = %s
        """, (attempt_id,))
        
        # Mark user_tasks as Completed
        cursor.execute("""
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        """, (session['user_id'], task_name, 'Completed'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Saved writing submitted successfully', 
            'attempt_id': attempt_id, 
            'attempt_number': attempt_number
        })
    except Exception as e:
        print(f"Error submitting saved writing: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/save-existing-writing-progress', methods=['POST'])
def save_existing_writing_progress():
    """Save existing writing progress without uploading a new file"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    task_name = data.get('task_name', 'Writing Task')
    
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get task_id
        cursor.execute("SELECT id FROM tasks WHERE task_name = %s", (task_name,))
        task_row = cursor.fetchone()
        if not task_row:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        task_id = task_row['id']
        
        # Get the latest IN PROGRESS attempt
        cursor.execute("""
            SELECT id, attempt_number FROM user_task_attempts 
            WHERE user_id = %s AND task_id = %s AND status = 'In Progress'
            ORDER BY attempt_number DESC LIMIT 1
        """, (session['user_id'], task_id))
        
        attempt_row = cursor.fetchone()
        if not attempt_row:
            return jsonify({'success': False, 'message': 'No saved progress found'}), 404
        
        attempt_id = attempt_row['id']
        attempt_number = attempt_row['attempt_number']
        
        # Update the writing sample uploaded_at timestamp (essentially a no-op but updates timestamp)
        cursor.execute("""
            UPDATE writing_samples 
            SET uploaded_at = NOW()
            WHERE attempt_id = %s
        """, (attempt_id,))
        
        # Mark user_tasks as In Progress (ensure it stays in progress)
        cursor.execute("""
            INSERT INTO user_tasks (user_id, task_name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = CURRENT_TIMESTAMP
        """, (session['user_id'], task_name, 'In Progress'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Progress saved successfully', 
            'attempt_id': attempt_id, 
            'attempt_number': attempt_number
        })
    except Exception as e:
        print(f"Error saving existing writing progress: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)