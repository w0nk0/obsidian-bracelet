# API Documentation

## Authentication
All API requests require authentication using Bearer tokens:

```
Authorization: Bearer <your_token_here>
```

## Endpoints

### Users
- `GET /api/v1/users/{id}` - Get user by ID
- `POST /api/v1/users` - Create new user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Products
- `GET /api/v1/products` - List all products
- `GET /api/v1/products/{id}` - Get product details
- `POST /api/v1/products` - Create product
- `PUT /api/v1/products/{id}` - Update product

### Orders
- `GET /api/v1/orders` - List orders (paginated)
- `POST /api/v1/orders` - Create new order
- `GET /api/v1/orders/{id}` - Get order details

## Rate Limiting
- 100 requests per minute for authenticated users
- 10 requests per minute for anonymous users
- Headers included:
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

## Error Handling
Standard HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## SDKs and Libraries
- **Python**: `pip install our-api-client`
- **JavaScript**: `npm install our-api-sdk`
- **PHP**: Available via Composer
- **Java**: Maven dependency available

## Support
For API support: api-support@company.com
For partnership inquiries: partnerships@company.com