# Multi-stage Dockerfile for React Frontend
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Nginx production server
FROM nginx:1.25-alpine

# Copy custom secure Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
