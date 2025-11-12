FROM python:3.10-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema para WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    zlib1g-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    libxml2-dev \
    libxslt1-dev \
    pkg-config \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Expor porta
EXPOSE 8000

# Entrypoint que executa migrações e depois o servidor
ENTRYPOINT ["sh", "-c"]
CMD ["python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

