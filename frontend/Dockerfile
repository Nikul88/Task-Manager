FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app
RUN npm install -g serve && apk add --no-cache gettext

COPY --from=build /app/dist/frontend/browser ./public
COPY env.js.template ./public/env.js.template

CMD ["sh", "-c", "export PORT=${PORT:-8080}; export API_URL=${API_URL:-http://localhost:8000/api}; envsubst '${API_URL}' < ./public/env.js.template > ./public/env.js && serve -s ./public -l ${PORT}"]
