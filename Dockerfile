# Use a light Python image
FROM python:3.9-slim

# Create keyrings directory for apt (needed for Dart)
RUN mkdir -p /usr/share/keyrings

# Install standard packages (Removed kotlin, added cargo just in case)
RUN apt-get update && apt-get install -y \
    gcc g++ default-jdk-headless sqlite3 golang-go rustc cargo ruby php-cli mono-mcs mono-runtime \
    r-base scala lua5.3 julia perl ghc nodejs npm wget unzip apt-transport-https gnupg2 curl \
    && rm -rf /var/lib/apt/lists/*

# Install Kotlin manually (Not in Debian repositories)
RUN wget -q https://github.com/JetBrains/kotlin/releases/download/v1.9.22/kotlin-compiler-1.9.22.zip && \
    unzip -q kotlin-compiler-1.9.22.zip -d /opt/ && \
    rm kotlin-compiler-1.9.22.zip

# Install TypeScript globally
RUN npm install -g typescript ts-node

# Install Dart SDK
RUN wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/dart.gpg && \
    echo 'deb [signed-by=/usr/share/keyrings/dart.gpg arch=amd64] https://storage.googleapis.com/download.dartlang.org/linux/debian stable main' | tee /etc/apt/sources.list.d/dart_stable.list && \
    apt-get update && apt-get install -y dart && rm -rf /var/lib/apt/lists/*

# Add Kotlin and Dart to PATH
ENV PATH="$PATH:/opt/kotlinc/bin:/usr/lib/dart/bin"

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
