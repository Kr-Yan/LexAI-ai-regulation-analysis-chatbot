FROM  node:18-alpine
#create an app directory and enter in it
WORKDIR /app

# copy package.json file
COPY package.json package-lock.json* ./

# install dependencies
RUN npm install --frozen-lockfile

# copy application code
COPY . .

# Build the application in compiled jsx files(mini)
RUN npm run build

# use nginx to serve the built app
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html

# copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
