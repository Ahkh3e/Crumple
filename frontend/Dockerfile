FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Create static directory if it doesn't exist
RUN mkdir -p /app/static

EXPOSE 3000

CMD ["flask", "run", "--host=0.0.0.0", "--port=3000"]
