# API Documentation

## GET /health

    {"status": "ok"}

## GET /cycle/status

    {
      "cycle_id": "uuid",
      "status": "idle|active|completed|failed|backpressure",
      "execution_count": 0,
      "error": null
    }
