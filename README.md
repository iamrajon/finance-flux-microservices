# Smart Expense Tracker

A microservices-based expense tracking application built with modern technologies including Django, FastAPI, RabbitMQ, and PostgreSQL. This project demonstrates event-driven architecture, API gateway patterns, and containerized deployment.

## 🏗️ Architecture

This application follows a microservices architecture with the following services:

- **API Gateway** (FastAPI) - Central entry point for all client requests
- **Auth Service** (Django) - User authentication and authorization with JWT
- **Expense Service** (FastAPI) - Expense and category management
- **Analytics Service** (Django) - Expense analytics and reporting
- **Notification Service** (FastAPI) - Email notifications via RabbitMQ events

## 🚀 Tech Stack

- **Backend Frameworks**: Django, FastAPI
- **Message Broker**: RabbitMQ
- **Databases**: PostgreSQL (separate DB per service)
- **Caching**: Redis
- **Authentication**: JWT (JSON Web Tokens)
- **Containerization**: Docker, Docker Compose
- **API Documentation**: OpenAPI/Swagger

## 📋 Features

- ✅ User registration and authentication
- ✅ JWT-based authorization
- ✅ Expense tracking with categories
- ✅ Analytics and spending insights
- ✅ Event-driven notifications
- ✅ API Gateway with rate limiting
- ✅ Microservices architecture
- ✅ Containerized deployment

## 🛠️ Prerequisites

- Docker Desktop
- Docker Compose
- Git

## ⚡ Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smart-expense-tracker.git
   cd smart-expense-tracker
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the services**
   - API Gateway: http://localhost:8000
   - Auth Service: http://localhost:8001
   - Expense Service: http://localhost:8002
   - Analytics Service: http://localhost:8003
   - Notification Service: http://localhost:8004
   - RabbitMQ Management: http://localhost:15672 (guest/guest)

## 📚 API Documentation

Once the services are running, access the interactive API documentation:

- API Gateway: http://localhost:8000/docs
- Expense Service: http://localhost:8002/docs
- Notification Service: http://localhost:8004/docs

## 🔧 Configuration

### Email Notifications

To enable email notifications, configure SMTP settings in your `.env` file. See [EMAIL_SETUP_GUIDE.md](EMAIL_SETUP_GUIDE.md) for detailed instructions.

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```env
# JWT Secret
JWT_SECRET_KEY=your-secret-key

# RabbitMQ
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Database credentials for each service
AUTH_DB_NAME=auth_db
EXPENSE_DB_NAME=expense_db
ANALYTICS_DB_NAME=analytics_db
```

## 🧪 Testing

Test the API endpoints using the provided `api-test.http` file with REST Client extension in VS Code, or use tools like Postman or curl.

### Example: Register a User

```bash
POST http://localhost:8000/api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "testuser",
  "name": "Test User",
  "password": "SecurePass123!",
  "password2": "SecurePass123!"
}
```

## 📊 Project Structure

```
Finance_Flux/
├── api-gateway/          # FastAPI gateway service
├── services/
│   ├── auth-service/     # Django authentication service
│   ├── expense-service/  # FastAPI expense management
│   ├── analytics-service/# Django analytics service
│   └── notification-service/ # FastAPI notification service
├── docker-compose.yml    # Docker orchestration
├── .env.example          # Environment variables template
└── README.md
```

## 🔄 Event-Driven Architecture

The application uses RabbitMQ for asynchronous event processing:

- **User Registration** → Welcome email notification
- **Expense Creation** → Analytics data update
- **User Updates** → Profile synchronization across services

## 🛡️ Security Features

- JWT-based authentication
- Password hashing with Django's built-in security
- Environment-based configuration
- API rate limiting
- CORS configuration
- Separate databases per service

## 📝 Development

### Running Individual Services

```bash
# Start only specific services
docker-compose up -d auth-service expense-service

# View logs
docker logs -f auth-service

# Rebuild a service
docker-compose up -d --build notification-service
```

### Database Migrations

```bash
# Auth service migrations
docker exec auth-service python manage.py makemigrations
docker exec auth-service python manage.py migrate

# Analytics service migrations
docker exec analytics-service python manage.py makemigrations
docker exec analytics-service python manage.py migrate
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)

## 🙏 Acknowledgments

- Built as a learning project to understand microservices architecture
- Inspired by modern cloud-native application patterns
- Uses industry-standard tools and best practices

---

**Note**: This is a portfolio/learning project demonstrating microservices architecture, event-driven design, and containerization best practices.
