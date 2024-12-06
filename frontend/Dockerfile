   # Use an official Node.js runtime as a parent image
   FROM node:18-alpine

   # Set the working directory in the container
   WORKDIR /app

   # Copy package.json and package-lock.json
   COPY package*.json ./

   # Install dependencies
   RUN npm install

   # Copy the rest of the application code
   COPY . .

   # Build the app for production
   RUN npm run build

   # Serve the app using a simple HTTP server
   RUN npm install -g serve

   # Expose the port the app runs on
   EXPOSE 3000

   # Command to run the application
   CMD ["serve", "-s", "build"]