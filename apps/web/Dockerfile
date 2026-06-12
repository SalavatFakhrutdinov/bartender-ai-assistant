FROM node:20-slim AS builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy shared package
COPY packages/shared-ts /app/packages/shared-ts
RUN cd /app/packages/shared-ts && pnpm install && pnpm build

# Copy web app
COPY apps/web/package.json apps/web/pnpm-lock.yaml* /app/apps/web/
WORKDIR /app/apps/web
RUN pnpm install

COPY apps/web /app/apps/web
RUN pnpm build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

COPY --from=builder /app/apps/web/.next /app/.next
COPY --from=builder /app/apps/web/package.json /app/package.json
COPY --from=builder /app/apps/web/public /app/public
COPY --from=builder /app/apps/web/node_modules /app/node_modules

EXPOSE 3000

CMD ["pnpm", "start"]
