FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies
# We use pip to install the current directory which contains pyproject.toml
RUN pip install --no-cache-dir .

# Expose the port the app runs on
EXPOSE 8000

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Run the application via entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
