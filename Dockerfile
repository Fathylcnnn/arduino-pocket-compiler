FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/local/bin sh

RUN arduino-cli config init && \
    arduino-cli config set board_manager.additional_urls \
      "https://arduino.esp8266.com/stable/package_esp8266com_index.json,https://espressif.github.io/arduino-esp32/package_esp32_index.json"

RUN arduino-cli core update-index || true

RUN arduino-cli core install arduino:avr
RUN arduino-cli core install esp8266:esp8266
RUN arduino-cli core install esp32:esp32 || echo "ESP32 atlandı"

WORKDIR /app
COPY compiler_server.py /app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "compiler_server.py"]
