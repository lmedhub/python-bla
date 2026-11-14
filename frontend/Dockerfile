# Build the frontend with Node, then serve the static files with nginx as a non-root user.

# --- build ---------------------------------------------------------------------
FROM node:22.23.5-alpine AS build
WORKDIR /app
# Only the dependency files first: this layer stays cached until package-lock.json changes.
# .npmrc pins the public registry.
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
RUN npm run build

# --- serve: nginx only, no Node ------------------------------------------------
# The unprivileged image runs nginx as a non-root user, listening on 8080.
FROM nginxinc/nginx-unprivileged:1.31.7-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
