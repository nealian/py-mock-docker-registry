from datetime import timedelta

DEFAULT_TOKEN_VALIDITY_PERIOD = timedelta(minutes=30)
ALGORITHM = 'HS256'
SECRET_KEY = '0f0f0f0f1e1e1e1e2d2d2d2d3c3c3c3c4b4b4b4b5a5a5a5a6060606079797979'
AUDIENCE = 'py-mock-docker-registry'
ISSUER = 'py-mock-docker-registry.example.com'
