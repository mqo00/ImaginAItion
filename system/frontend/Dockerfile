# Use Node.js base image
FROM node:18

# Set the working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Expose frontend port
EXPOSE 5173

# Run Vite development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
