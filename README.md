# B2Broker Django REST Framework Project

A basic Django REST Framework project with PostgreSQL database configuration.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure PostgreSQL database:
   - Create a database named `b2broker_db`
   - Update database credentials in `b2broker_project/settings.py` if needed

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Create superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```

6. Run development server:
   ```bash
   python manage.py runserver
   ```

## Project Structure

- `b2broker_project/` - Main Django project configuration
- `api/` - Django app for API endpoints
- `manage.py` - Django management script
- `requirements.txt` - Python dependencies

## Database Configuration

Default PostgreSQL settings in `settings.py`:
- Database: `b2broker_db`
- User: `postgres`
- Password: `password`
- Host: `localhost`
- Port: `5432`

Update these settings according to your PostgreSQL setup. 