# GoGoCarpool - Carpooling Platform

Django REST API backend for a carpooling service.

## Tech Stack

- Django 5.2
- Django REST Framework
- SQLite (development)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## API Documentation

API is available at: `http://localhost:8000/api/`

### Main Endpoints

- `/api/auth/` - Authentication
- `/api/trips/` - Trips management
- `/api/bookings/` - Bookings
- `/api/users/` - User profiles
- `/api/cities/` - Cities
- `/api/ratings/` - Ratings
- `/api/notifications/` - Notifications

## Project Structure

```
carpooling/
├── models/         # Data models
├── serializers/    # DRF serializers
└── views/          # API views
```

## License

Private project
