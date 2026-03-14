FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* .npmrc* ./
RUN npm install --silent --no-progress || yarn install --frozen-lockfile || true

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
