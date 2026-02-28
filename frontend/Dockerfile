FROM node:20-alpine

RUN apk add --no-cache wget

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
EXPOSE 3000

# Listen on all interfaces so the app is reachable from the host
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
