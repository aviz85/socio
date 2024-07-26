# Socio

Socio is a Django-based social media backend API that provides functionality for user registration, posting, commenting, liking, and a customizable feed algorithm.

## Features

- User registration and authentication
- Create, read, update, and delete posts
- Create nested comments on posts
- Like posts and comments
- Activity tracking
- Customizable feed algorithms
- RESTful API

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/aviz85/socio.git
   cd socio
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Start the development server:
   ```
   python manage.py runserver
   ```

## API Endpoints

- `/api/register/`: User registration
- `/api/posts/`: CRUD operations for posts
- `/api/comments/`: CRUD operations for comments
- `/api/likes/`: Create and delete likes
- `/api/activities/feed/`: Get personalized feed
- `/api/feed-algorithms/`: CRUD operations for feed algorithms

## Testing

Run the test suite with:

```
python manage.py test
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open-source and available under the [MIT License](LICENSE).