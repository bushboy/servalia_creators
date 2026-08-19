# Build stage — compile the SPA (OIDC values can still be baked, but runtime
# config from docker-entrypoint.sh overrides them in the browser).
FROM node:22-alpine AS builder

ARG VITE_API_BASE_URL=/api

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Serve stage — nginx + runtime config injection
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
