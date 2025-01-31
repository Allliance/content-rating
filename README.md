# Content Rating Service

A high-performance, production-ready rating system built with Django and Apache Kafka, designed for scalability and real-time processing.

## 🚀 Features

- **Asynchronous Rating Processing**: Utilizes Kafka for efficient batch processing of ratings
- **Anomaly Detection**: Intelligent system to identify and handle suspicious rating patterns
- **Real-time Analytics**: Instant access to content statistics and rating metrics
- **High Performance**: Optimized for large-scale production environments
- **Docker Ready**: Fully containerized setup for easy deployment
- **Monitoring**: Built-in Prometheus integration for system metrics

## 🏗️ Architecture

The service is built with a microservices architecture, utilizing:

- **Django**: Core application framework
- **Apache Kafka**: Message broker for rating processing
- **PostgreSQL**: Primary data store
- **Prometheus**: Metrics and monitoring
- **Nginx**: Reverse proxy and static file serving

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone https://github.com/allliance/content-rating.git
cd content-rating
```

2. Start the service:
```bash
docker-compose up -d
```

3. The application will be available at:
- API: http://localhost:80
- Prometheus: http://localhost:9090

## 🔌 API Endpoints

### Content Management

```
GET /contents/
- List all contents with their ratings
- Supports pagination and filtering

GET /contents/{content_id}/
- Retrieve specific content details
- Includes rating statistics

POST /contents/create/
- Create new content
- Required fields: title, text

POST /contents/rate/
- Rate existing content
- Required fields: content_id, rating (0-5)
```

## 🔧 Configuration
The service can be configured through environment variables:

```
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
DATABASE_URL=postgres
POSTGRES_DB=contents_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
REDIS_URL=redis://redis:6379/1
```

## 🔒 Security
- SSL/TLS encryption for all external communications
- JWT-based authentication
- Anomaly detection for suspicious rating patterns

## Anomaly Detection
In order to detect malicious rating behavior, when a user first rates a content, it is added to the database, but not taken into account while calculating metrics for that content (processed field of the rating object is False). When the `rating_processor` encounters the rate request, it investigates the recent (last hour) ratings with the same rating value for this content. If all the recent ratings for this content were less than 10 (`MIN_RATE_COUNT`), then it cannot be verified if this rating is malicous. Otherwise, if the portion of the ratings with this value over all recent ratings was above 0.85 (`ANOMALY_THRESHOLD`), the rating would be penalized by assigning a low weight of 0.001 (`ANOMALY_WEIGHT_PENALTY`).

## Performance Consideration for large number of ratings
In order to handle real-time analytics (being able to sort the contents by rating count and rating value), these fields are stored inside the Content model, and are updated in batches by the kafka consumers (rating_processor).


## 📈 Scaling
The service is designed to scale horizontally:

1. Kafka partitioning for parallel processing
2. Stateless application design
4. Database connection pooling