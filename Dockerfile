FROM texlive/texlive:latest

USER root

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8

# Python und eine getrennte Umgebung für die Python-Pakete installieren.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 python3-venv fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN /opt/venv/bin/python -m pip install --no-cache-dir \
    -r /app/requirements.txt

# Fira Sans aus TeX Live für die Schrifterkennung registrieren.
RUN mkdir -p /usr/local/share/fonts/fira \
    && find "$(kpsewhich -var-value=TEXMFDIST)/fonts/opentype" \
       -type f -name 'FiraSans-*.otf' \
       -exec cp {} /usr/local/share/fonts/fira/ \; \
    && test -f /usr/local/share/fonts/fira/FiraSans-Regular.otf \
    && fc-cache -f \
    && luaotfload-tool --update

COPY generate.py LICENSE /app/

# Prüfen, ob das Programm mit seinen Python-Abhängigkeiten startet.
RUN /opt/venv/bin/python /app/generate.py --help

WORKDIR /data

ENTRYPOINT ["/opt/venv/bin/python", "/app/generate.py"]
CMD ["/data/lebenslauf.md"]
