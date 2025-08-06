# Dyslexia Study Website - Backend Setup

This is the backend for the dyslexia research study website, built with Flask and MySQL.

## Prerequisites

- Python 3.8 or higher
- MySQL Server
- pip (Python package manager)

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up MySQL Database

1. Start your MySQL server
2. Open MySQL command line or MySQL Workbench
3. Run the database setup script:

```bash
mysql -u root -p < database_setup.sql
```

Or copy and paste the contents of `database_setup.sql` into your MySQL client.

### 3. Configure Database Connection

Edit the `DB_CONFIG` in `app.py` to match your MySQL settings:

```python
DB_CONFIG = {
    "host": "localhost",      # Change if using a remote server
    "user": "root",           # Change to your MySQL username
    "password": "itaCHI#1",   # Change to your MySQL password
    "database": "dyslexia_study"
}
```

### 4. Run the Flask Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Registration
- **POST** `/api/register`
- **Body**: `{"username": "...", "email": "...", "phone": "...", "password": "...", "gender": "...", "dob": "..."}`

### Login
- **POST** `/api/login`
- **Body**: `{"email": "...", "password": "..."}`

### Logout
- **POST** `/api/logout`

### Get User Info
- **GET** `/api/user-info`

### Test Database Connection
- **GET** `/test-db`

## Database Schema

### Users Table
- `id` (Primary Key)
- `username` (VARCHAR)
- `email` (VARCHAR, Unique)
- `phone_number` (VARCHAR)
- `password_hash` (VARCHAR)
- `date_of_birth` (DATE)
- `gender` (VARCHAR)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Consent Data Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `consent_given` (BOOLEAN)
- `consent_date` (TIMESTAMP)
- `ip_address` (VARCHAR)
- `user_agent` (TEXT)

### Demographics Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `date_of_birth` (DATE)
- `gender` (VARCHAR)
- `native_language` (VARCHAR)
- `education_level` (VARCHAR)
- `dyslexia_status` (VARCHAR)
- `created_at` (TIMESTAMP)

## Security Features

- Password hashing using bcrypt
- Session management
- Input validation
- CORS enabled for frontend integration

## Troubleshooting

1. **Database Connection Error**: Check your MySQL server is running and credentials are correct
2. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`
3. **Port Already in Use**: Change the port in `app.py` or kill the process using port 5000

## Development

- The application runs in debug mode by default
- Logs are printed to the console
- Database errors are caught and logged 