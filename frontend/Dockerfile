# Stage 1: build the static site. VITE_* values are baked in at build time.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Stage 2: serve the built files with Vite's static preview server (no extra web server needed).
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY vite.config.js ./
COPY --from=build /app/dist ./dist
# Vite writes a temporary file next to its config, so the runtime user must own the directory.
RUN chown -R node:node /app
USER node
EXPOSE 5173
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]
