# Step 1: build the React app into plain HTML/JS/CSS files
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# the API key is baked into the build (docker-compose passes it in)
ARG API_KEY
ENV API_KEY=$API_KEY
RUN npm run build

# Step 2: serve those files with nginx (small and fast)
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
