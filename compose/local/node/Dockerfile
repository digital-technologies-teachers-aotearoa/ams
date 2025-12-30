FROM docker.io/node:25.2-bookworm-slim

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
USER node

ENV PATH=./node_modules/.bin/:$PATH

ENTRYPOINT ["/entrypoint.sh"]
