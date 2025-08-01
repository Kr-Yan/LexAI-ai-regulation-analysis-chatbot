FROM python:3.9-slim

# set and enter the working directory
WORKDIR /app

# install system dependencies
RUN apt-get update&& apt-get install -y \
    gcc\
    g++\
    && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt to app
COPY requirements.txt .

# install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# COPY ALL CODE
COPY . .

# Create necessary dependencies
RUN mkdir -p data/vector_db temp

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

