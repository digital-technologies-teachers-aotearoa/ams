FROM docker.io/node:25.7-bookworm-slim

# Allow conditional user setting (default to node, can override with --build-arg RUN_USER=root)
ARG RUN_USER=node

WORKDIR /app

# Change ownership of the working directory to the existing node user (uid 1000, gid 1000)
RUN chown -R node:node /app

# Switch to non-root user
USER node

COPY --chown=node:node ./package.json /app

RUN npm install && npm cache clean --force

COPY --chown=node:node ./compose/local/node/entrypoint.sh /entrypoint.sh

# Switch to root temporarily to chmod the entrypoint
USER root
RUN chmod +x /entrypoint.sh
USER ${RUN_USER}

ENV PATH=./node_modules/.bin/:$PATH

ENTRYPOINT ["/entrypoint.sh"]
