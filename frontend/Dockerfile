FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

RUN apk add --no-cache gettext

COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY env.js.template /usr/share/nginx/html/env.js.template

CMD ["sh", "-c", "export PORT=${PORT:-8080}; export API_URL=${API_URL:-http://localhost:8000/api}; envsubst '${PORT} ${API_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && envsubst '${API_URL}' < /usr/share/nginx/html/env.js.template > /usr/share/nginx/html/env.js && nginx -g 'daemon off;'"]
