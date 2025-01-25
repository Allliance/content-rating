# Content Rating

A simple and efficient content rating system built using Django Rest Framework.

## Implementation Notes

### Models
To keep things streamlined, this system uses only two models:

- **Content**: Represents the essential features of a piece of content.
- **Rating**: Stores the ratings submitted for specific content.

### Performance Considerations
To optimize the performance of the `content-list` API, Redis caching is employed. Each piece of content stored in the cache includes a `rating_stats` key-value pair, which contains:
- The (weighted) average rating for the content.
- The total number of ratings submitted.

The cache entry has a Time-To-Live (TTL) of 1 hour. To maintain cache consistency, a signal receiver is triggered whenever a rating is created or updated. This invalidates the cached `rating_stats` for the content. The cache isn't updated immediately when a rating is submitted to favor a lazy evaluation approach.

Noteworthy that it was possible to store the ratings_stats inside the Content model as a field. However, in that case, the lazy evaluation approach would not be straightforward, as whenever a rating object was created, its corresponding content had to be updated.

### Handling Rating Bombing
To address rating manipulation, such as a sudden surge of upvotes or downvotes for a piece of content, a weight decay mechanism is applied. The `Rating` model includes a `weight` field, which is a value between 0 and 1. Additionally, a `RATE_LIMIT_PER_HOUR` (limit) constant (default: `10000`) is defined in `constants.py`. 

When a user submits a rating, the following formula determines the weight:


$$w = \frac{\max(1, limit - recent)}{limit}$$

Here:
- `recent` refers to the number of ratings with the same value submitted within the past hour.
- If a large number of ratings are submitted within an hour, their importance diminishes due to reduced weight.

It’s worth noting that there’s no universal solution to prevent rating bombing entirely. For instance, users may still schedule their submissions to spread them over time, bypassing some of these safeguards.

## Usage


### Running the Application Locally
To run the application locally, use the following commands:

```bash
python manage.py makemigrations contents
python manage.py migrate
python manage.py runserver
```

**Important Note**:
- Make sure that a redis server is up in your local system, listening on port 6379.

### Running the Application Using Docker
To run the application with Docker, simply execute:

```bash
docker compose up web
```

### Populating the Database
To populate the database with sample data, execute:

```bash
python manage.py populate_db
```


