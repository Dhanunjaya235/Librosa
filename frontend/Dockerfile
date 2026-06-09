# syntax=docker/dockerfile:1

FROM --platform=linux/amd64 node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
RUN npm run build

FROM --platform=linux/amd64 nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Bypass docker-entrypoint.sh to avoid exec format errors from arch/cache mismatches
ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]

EXPOSE 80
