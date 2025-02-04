# Usa un'immagine Python ufficiale
FROM python:3.11-slim

# Aggiorna i pacchetti e installa Tesseract OCR e altre dipendenze
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && apt-get clean

# Imposta la directory di lavoro
WORKDIR /app

# Copia tutti i file del progetto nella directory di lavoro
COPY . .

# Rendi eseguibile lo script di startup (se necessario)
RUN chmod +x startup.sh

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando per avviare l'applicazione
CMD ["python3", "main.py"]
