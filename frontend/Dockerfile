# nxcare_fe - built static assets served by nginx (see docker-compose.yml)
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Without this ARG declaration, docker-compose.yml's `build.args.VITE_API_BASE_URL` is silently
# dropped (an undeclared build arg is ignored, not an error) and ENV below resolves to an empty
# string - Vite then bakes "" into the bundle instead of the backend URL, and every fetch in the
# browser goes to a relative path on nxcare_fe itself instead of nxcare_be.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
