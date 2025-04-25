# Prometeo API Backend

This is the backend service for the Prometeo Dashboard application, providing an API for client data analysis and management.

## Setup

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 14 or higher

### Automatic Setup (Recommended)

Use the automated setup script to configure your environment:

```bash
cd "05. Dashboard/backend"
chmod +x check_env.sh
./check_env.sh
```

This script will:
1. Check if Python is installed
2. Create a virtual environment if it doesn't exist
3. Install all required dependencies
4. Configure the development environment

### Manual Installation

If you prefer a manual setup:

1. Clone the repository and navigate to the backend directory:

```bash
cd "05. Dashboard/backend"
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
```

3. Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

4. Configure the database:

Make sure you have a PostgreSQL database named `prometeo_db` accessible by the user `postgres` with password `1111`.

## Usage

#### Testing Database Connection

Run the database connection test script:

```bash
./db_connect.sh
```

This script will verify that your database connection is working and show the available tables.

#### Starting the Development Server

Start the development server with:

```bash
./start_dev.sh
```

The API will be available at http://localhost:8000

#### API Documentation

Once the server is running, you can access the API documentation at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Project Structure

- `app/` - Application code
  - `api.py` - FastAPI application and endpoints
  - `database.py` - Database configuration
  - `models.py` - SQLAlchemy ORM models
  - `schemas.py` - Pydantic models for API
  - `ml_service.py` - Machine learning services
- `alembic/` - Database migration scripts
- `db_connect.sh` - Database connection testing script
- `start_dev.sh` - Development server startup script
- `check_env.sh` - Environment setup and verification script

## Development

### Database Migrations

To create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

To apply migrations:

```bash
alembic upgrade head
``` 