FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY main.py streamlit_app.py /app/

RUN python -m pip install --upgrade pip && \
    python -m pip install .

RUN chown -R app:app /app
USER app

EXPOSE 8501

CMD ["python", "main.py", "--no-viz"]

