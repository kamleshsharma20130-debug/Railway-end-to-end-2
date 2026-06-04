FROM python:3.11-slim

# ==================================================
# PYTHON SETTINGS
# ==================================================

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# ==================================================
# INSTALL CHROMIUM + DRIVER + REQUIRED LIBS
# ==================================================

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libu2f-udev \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# CHROME PATHS
# ==================================================

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# ==================================================
# WORK DIRECTORY
# ==================================================

WORKDIR /app

# ==================================================
# COPY FILES
# ==================================================

COPY . .

# ==================================================
# INSTALL PYTHON PACKAGES
# ==================================================

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# ==================================================
# START BOT
# ==================================================

CMD ["python", "-u", "main.py"]
