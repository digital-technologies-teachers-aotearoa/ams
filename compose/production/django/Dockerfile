###################################################################################################
# Production Django Image (Multi-Stage Build)
# ---------------------------------------------------------------------------------
# Overview of stages:
# 1. client-builder      : Uses a Node image to install JS dependencies and build static assets.
# 2. python (base alias) : Shared slim Python base image (Bookworm) to avoid repetition.
# 3. python-build-stage  : Installs build tooling and produces cached wheels for Python deps.
# 4. python-run-stage    : Final runtime image: installs wheels, adds system/runtime deps, copies
#                          application code and built assets, sets up a non-root user, and defines
#                          the container entrypoint.
#
# Why this structure?
# - Smaller final image: build dependencies (gcc, headers) stay only in the build stage.
# - Better layer caching: wheels are built separately so most rebuilds reuse them unless
#   requirements change.
# - Faster deployments: compiling assets & dependencies happens once per change set.
# - Security: final image runs as an unprivileged 'django' user and excludes build toolchain.
#
# Wheel strategy:
#   We first COPY the requirements directory, then run `pip wheel` to pre-build wheels for every
#   dependency (and sub-dependency). In the final stage we install from those wheels using
#   --no-index so no network access is required during the runtime image build.
#
# Static assets:
#   Node builds front-end assets (e.g. via npm run build) in the client-builder stage; the built
#   output is copied into the final Python image alongside the Django code base.
#
# Internationalization:
#   `compilemessages` is invoked after dependencies are installed and the user context is set, to
#   ensure translation .mo files are present in the runtime image.
#
# Entrypoint / Start scripts:
#   Provided via compose/production/django. They are copied in, line endings normalized, and marked
#   executable. ENTRYPOINT launches the primary orchestration script.
#
# Environment variables:
#   BUILD_ENV controls which requirements file to use (e.g. production.txt). PYTHONUNBUFFERED and
#   PYTHONDONTWRITEBYTECODE are set for predictable logging and to avoid .pyc creation.
#
# Rebuild triggers (cache busting hints):
#   - Changes to package.json => re-run npm install + asset build.
#   - Changes to any requirements/*.txt => rebuild wheels layer.
#   - Changes to application code => only final copy layer invalidated.
#
###################################################################################################

# ---- Stage 1: Frontend asset build (Node) -------------------------------------------------------
FROM docker.io/node:24.6-bookworm-slim AS client-builder

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

COPY ./package.json ${APP_HOME}
# Install JS dependencies; cache will be reused unless package.json changes.
RUN npm install && npm cache clean --force
COPY . ${APP_HOME}
# Produce production-grade static assets (e.g. minified JS/CSS)
RUN npm run build

###################################################################################################
# Base Python image alias (shared between build & run stages) -------------------------------------
# Using a single alias lets us pin the version once and reuse it for consistency.
###################################################################################################
FROM docker.io/python:3.12.12-slim-bookworm AS python

###################################################################################################
# ---- Stage 2: Python build stage ---------------------------------------------------------------
# Installs compilation toolchain & headers needed to build wheels for all dependencies.
# All heavy build artifacts remain in this stage; only final wheels are copied forward.
###################################################################################################
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=production

# Install system packages required solely for building Python dependencies.
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg dependencies
  libpq-dev

# Copy requirements directory (contains production.txt etc.) early for layer caching.
COPY ./requirements .

# Build wheels for all direct + transitive dependencies; later we install without network access.
RUN pip wheel --wheel-dir /usr/src/app/wheels \
  -r ${BUILD_ENVIRONMENT}.txt


###################################################################################################
# ---- Stage 3: Python runtime stage -------------------------------------------------------------
# Lightweight final image: installs only runtime system packages, Python wheels, application code
# and built static assets. Creates non-root user 'django'.
###################################################################################################
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Create an unprivileged system user & group for running the application.
RUN addgroup --system django \
  && adduser --system --ingroup django django


# Install runtime system dependencies only (no build-essential here for smaller, safer image)
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  # entrypoint
  wait-for-it \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Copy built dependency wheels from the build stage.
COPY --from=python-build-stage /usr/src/app/wheels /wheels/

# Install Python dependencies from local wheels, then remove wheels to save space.
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/


# Copy and prepare entrypoint script.
COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint  # Normalize potential Windows line endings.
RUN chmod +x /entrypoint


# Copy and prepare start script.
COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start  # Normalize potential Windows line endings.
RUN chmod +x /start


# Copy application source code AND previously built static assets from client-builder stage.
COPY --from=client-builder --chown=django:django ${APP_HOME} ${APP_HOME}

# Ensure 'django' user owns the entire application directory tree.
RUN chown -R django:django ${APP_HOME}

USER django

# Compile translation message files with required settings blanked.
RUN DJANGO_SETTINGS_MODULE="config.settings.test" \
  DJANGO_MEDIA_PUBLIC_BUCKET_NAME="" \
  DJANGO_MEDIA_PUBLIC_ENDPOINT_URL="" \
  DJANGO_MEDIA_PUBLIC_ACCESS_KEY="" \
  DJANGO_MEDIA_PUBLIC_SECRET_KEY="" \
  DJANGO_MEDIA_PRIVATE_BUCKET_NAME="" \
  DJANGO_MEDIA_PRIVATE_ENDPOINT_URL="" \
  DJANGO_MEDIA_PRIVATE_ACCESS_KEY="" \
  DJANGO_MEDIA_PRIVATE_SECRET_KEY="" \
  python manage.py compilemessages

ENTRYPOINT ["/entrypoint"]
