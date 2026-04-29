FROM node:22-alpine AS build

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY apps/web/ .
RUN npm run build

FROM caddy:2-alpine

COPY --from=build /app/dist /srv
COPY ops/coolify/Caddyfile /etc/caddy/Caddyfile

EXPOSE 80
