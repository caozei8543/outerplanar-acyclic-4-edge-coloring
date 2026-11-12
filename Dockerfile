FROM python:3.13.5-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
RUN pip install --no-cache-dir '.[plot,test]'
COPY . .
CMD ["python", "-m", "pytest", "-q"]
