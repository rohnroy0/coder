FROM python:3.11-alpine
RUN apk add --no-cache gcc g++ musl-dev && adduser -D runner
USER runner
WORKDIR /app
CMD ["python", "main.py"]
