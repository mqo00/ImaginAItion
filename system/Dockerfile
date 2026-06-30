FROM node:18 AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY frontend ./
RUN npm run build

FROM python:3.12 AS backend

WORKDIR /app
COPY backend/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY backend ./

FROM python:3.12

WORKDIR /app

# Copy backend and frontend builds
COPY --from=backend /app /app
COPY --from=frontend-builder /app/frontend/dist /app/frontend-dist

RUN python -m pip install --no-cache-dir -r /app/requirements.txt && python -m pip list

EXPOSE 5001

CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port 5001 --ws auto --reload "]
