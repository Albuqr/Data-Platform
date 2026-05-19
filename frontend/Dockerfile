FROM python:3.11-slim
WORKDIR /frontend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY templates/ ./templates/
COPY static/ ./static/
COPY app.py .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]