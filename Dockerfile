# Use Microsoft's Playwright image which has all browser dependencies pre-installed
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Make sure Playwright browsers are installed
RUN playwright install chromium

# Expose port 8080 as default
EXPOSE 8080

# Start the app - Railway provides $PORT at runtime, default to 8080
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --timeout 300 --workers 2
