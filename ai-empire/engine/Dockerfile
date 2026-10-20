FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY empire ./empire
RUN mkdir -p /app/data /app/workspace && useradd --create-home --uid 10001 empire && chown -R empire:empire /app
USER empire
EXPOSE 8000
CMD ["sh", "-c", "uvicorn empire.api:app --host ${EMPIRE_API_HOST:-127.0.0.1} --port 8000"]
