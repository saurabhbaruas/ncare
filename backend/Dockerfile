FROM python:3.12-slim
WORKDIR /app

# install the libraries first, so Docker can reuse this layer when only the code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# the app creates the tables and loads demo data by itself on start-up
# --forwarded-allow-ips: trust the X-Forwarded-For header that nginx adds, so the rate limiter
# and the login audit log see each user's real IP and not nginx's
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
