FROM python:3.11-slim

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# arduino-cli kur
RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/local/bin sh

# arduino-cli konfigürasyon ve platform kurulumu
RUN arduino-cli config init && \
    arduino-cli config set board_manager.additional_urls \
      "https://arduino.esp8266.com/stable/package_esp8266com_index.json,https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json" && \
    arduino-cli core update-index && \
    arduino-cli core install arduino:avr && \
    arduino-cli core install esp8266:esp8266 && \
    arduino-cli core install esp32:esp32

# Python uygulamasını kur
WORKDIR /app
COPY compiler_server.py /app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "compiler_server.py"]
