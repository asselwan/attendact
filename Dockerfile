FROM node:22-alpine AS web-build
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ .
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir uv

COPY apps/api/pyproject.toml .
COPY apps/api/src ./src
RUN uv pip install --system .

COPY --from=web-build /web/dist ./static

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
