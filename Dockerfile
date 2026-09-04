# Use a light Python image
FROM python:3.9-slim

# Install C, C++ compilers and Java JDK
# Using 'default-jdk-headless' ensures compatibility regardless of the version (21 or 25)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-jdk-headless \
    sqlite3 \
    golang-go \
    rustc \
    ruby \
    php-cli \
    mono-mcs \
    mono-runtime \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install dependencies (leverages layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
