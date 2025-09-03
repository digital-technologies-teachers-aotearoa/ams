# Deployment

## Production

By running an [AMS Docker image](https://ghcr.io/digital-technologies-teachers-aotearoa/ams-django), the software can be deployed in a production environment.
This can be run on any managed platform that supports Docker containers, such as [Digital Ocean](https://www.digitalocean.com/), or you can manage it yourself with a system such as [Kubernetes](https://kubernetes.io/).
The following environment variables are required:

| Variable | Example Value | Description |
|---|---|---|
| `POSTGRES_HOST` | `postgres` | The hostname of the PostgreSQL database server |
| `POSTGRES_PORT` | `5432` | The port of the PostgreSQL database server |
| `POSTGRES_DB` | `ams` | The database name of the PostgreSQL database server |
| `POSTGRES_USER` | `username` | The name of the user to access the PostgreSQL server |
| `POSTGRES_PASSWORD` | `password` | The password of the user to access the PostgreSQL |
| `DJANGO_SECRET_KEY` | `secret-key` | The Django secret key |
| `DJANGO_ADMIN_URL` | `admin/` | The URL for the Django admin |
| `DJANGO_ALLOWED_HOSTS` | `*` | The allowed hosts for Django |
| `MAILGUN_API_KEY` | `redacted-api-key` | The API key for Mailgun |
| `MAILGUN_DOMAIN` | `sandbox.mailgun.org` | The domain for Mailgun |
| `MAILGUN_API_URL` | `https://api.mailgun.net` | The API URL for Mailgun |
| `SENTRY_DSN` | `https://123@456.ingest.de.sentry.io/789` | The DSN value for Sentry observability |
