# Ryde Backend - RESTful API

A comprehensive RESTful API for user management and friendship features built with Django and Django REST Framework.

## Features

### Core Functionality
- **User Management**: Complete CRUD operations for user profiles
- **Authentication**: Token-based authentication with secure password handling
- **Friendship System**: Follow/following relationships with status management
- **Location Services**: Geographic coordinate support with distance calculations
- **Search & Filtering**: Advanced search and filtering capabilities

### Advanced Features
- **Nearby Friends**: Find friends within a specified radius using geographic coordinates
- **Comprehensive Logging**: Request/response logging with performance monitoring
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation
- **Unit Testing**: Comprehensive test coverage for all components
- **Admin Interface**: Django admin integration for data management

## Tech Stack

- **Python 3.12+**
- **Django 5.2+**
- **Django REST Framework 3.14+**
- **PostgreSQL** (Database)
- **Redis** (Caching & Task Queue)
- **Celery** (Background Tasks)
- **Geopy** (Geographic Calculations)

## Project Structure

```
challenge/
├── challenge/                 # Main project settings
│   ├── settings.py           # Django settings
│   ├── urls.py               # Main URL configuration
│   └── wsgi.py               # WSGI configuration
├── users/                    # User management app
│   ├── models.py             # Custom User model
│   ├── serializers.py        # User serializers
│   ├── views.py              # User API views
│   ├── permissions.py        # Custom permissions
│   ├── utils.py              # Utility functions
│   ├── middleware.py         # Request logging middleware
│   ├── admin.py              # Admin interface
│   └── tests.py              # User tests
├── friendships/              # Friendship management app
│   ├── models.py             # Friendship model
│   ├── serializers.py        # Friendship serializers
│   ├── views.py              # Friendship API views
│   ├── admin.py              # Admin interface
│   └── tests.py              # Friendship tests
├── manage.py                 # Django management script
├── pyproject.toml            # Project dependencies
└── README.md                 # This file
```

## Installation & Setup

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis (optional, for caching and Celery)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd challenge
```

### 2. Install Dependencies

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=ryde_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis Settings (optional)
REDIS_URL=redis://localhost:6379/0
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb ryde_db

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 5. Run the Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication

The API uses Token Authentication. Include the token in the Authorization header:

```
Authorization: Token <your-token>
```

### User Endpoints

#### User Registration
```http
POST /api/users/
Content-Type: application/json

{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "dob": "1990-01-01",
    "address": "123 Main St, City",
    "description": "User description",
    "latitude": 40.7128,
    "longitude": -74.0060
}
```

#### User Login
```http
POST /api/users/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

#### Get User Profile
```http
GET /api/users/me/
Authorization: Token <your-token>
```

#### Update User Profile
```http
PATCH /api/users/{user_id}/
Authorization: Token <your-token>
Content-Type: application/json

{
    "name": "Updated Name",
    "address": "Updated Address"
}
```

#### Search Users
```http
GET /api/users/search_by_name/?q=john
Authorization: Token <your-token>
```

#### Find Nearby Users
```http
GET /api/users/nearby_friends/?radius=10
Authorization: Token <your-token>
```

### Friendship Endpoints

#### Send Friendship Request
```http
POST /api/friendships/
Authorization: Token <your-token>
Content-Type: application/json

{
    "to_user": "user-uuid-here"
}
```

#### Get Friends List
```http
GET /api/friendships/friends/
Authorization: Token <your-token>
```

#### Get Pending Requests
```http
GET /api/friendships/pending_requests/
Authorization: Token <your-token>
```

#### Accept/Decline Friendship Request
```http
POST /api/friendships/{friendship_id}/action/
Authorization: Token <your-token>
Content-Type: application/json

{
    "action": "accept"  // or "decline", "block", "unblock"
}
```

#### Find Nearby Friends
```http
GET /api/friendships/nearby_friends/?radius=10
Authorization: Token <your-token>
```

## User Model Schema

```json
{
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "dob": "1990-01-01",
    "address": "123 Main St, City",
    "description": "User description",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "age": 34,
    "has_location": true
}
```

## Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test friendships

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## API Documentation (Swagger)

Access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

## Admin Interface

Access the Django admin interface at http://localhost:8000/admin/ using your superuser credentials.

## Logging

The application includes comprehensive logging:

- **File Logs**: `logs/django.log`
- **Console Logs**: Development server output
- **Request Logging**: All API requests and responses
- **Performance Monitoring**: Slow request detection

## Performance Features

- **Database Indexing**: Optimized queries with proper indexes
- **Caching**: Redis-based caching for frequently accessed data
- **Pagination**: API responses are paginated for better performance
- **Select Related**: Optimized database queries to reduce N+1 problems

## Security Features

- **Token Authentication**: Secure API access
- **Password Validation**: Strong password requirements
- **CORS Configuration**: Cross-origin request handling
- **Input Validation**: Comprehensive data validation
- **Permission System**: Role-based access control

## Deployment

### Production Settings

Update `settings.py` for production:

```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
SECRET_KEY = 'your-production-secret-key'

# Use environment variables for sensitive data
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}
```

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "challenge.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact:
- Email: contact@ryde.com
- Documentation: http://localhost:8000/swagger/