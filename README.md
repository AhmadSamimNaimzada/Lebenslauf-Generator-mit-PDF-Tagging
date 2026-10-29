# Lebenslauf-Generator mit PDF-Tagging

Ein Python-Werkzeug, das einen Lebenslauf aus einer Markdown-Datei als getaggtes PDF erstellt. Docker stellt Python, LuaLaTeX, die benötigten Pakete und die Schriftart Fira Sans gemeinsam bereit.

## Projektziel

Lebensläufe sollen sich als Text bearbeiten und anschließend mit einem einheitlichen Layout als PDF erzeugen lassen. Das Docker-Image ermöglicht die Ausführung, ohne Python oder LaTeX auf dem Zielrechner einzeln einzurichten.

## Funktionen

- Kontaktdaten und Einstellungen aus einem YAML-Kopf einlesen
- Lebenslauf-Inhalte aus Markdown verarbeiten
- LaTeX-Code erzeugen und mit LuaLaTeX in zwei Durchläufen kompilieren
- PDF-Strukturtags über die LaTeX-Tagging-Funktionen erzeugen
- Fehlermeldungen bei ungültigen Eingaben oder fehlgeschlagener Kompilierung ausgeben

Die erzeugten Strukturtags allein sind kein Nachweis vollständiger PDF/UA-Konformität.

## Verwendete Technologien

Python · PyYAML · Docker · LuaLaTeX · Markdown · YAML

## Mit Docker verwenden

Voraussetzung ist eine laufende Docker-Installation. Die folgenden Befehle sind für Linux gedacht.

Im Projektordner das Image erstellen:

```bash
sudo docker build -t lebenslauf-generator:1.0 .
```

Anschließend den Beispiel-Lebenslauf erstellen:

```bash
sudo docker run --rm \
  --network none \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e TEXMFVAR=/tmp/texmf-var \
  --mount "type=bind,source=$PWD,target=/data" \
  lebenslauf-generator:1.0
```

Die Dateien `lebenslauf.pdf` und `lebenslauf.tex` entstehen im Projektordner. Vorhandene Ausgaben werden überschrieben.

Der erste Image-Build lädt eine vollständige TeX-Live-Umgebung herunter und benötigt mehrere GB Speicherplatz. Die anschließende PDF-Erstellung erfolgt ohne Netzwerkzugriff.

## Eigene Daten verwenden

Die Datei `lebenslauf.md` enthält die persönlichen Angaben und den Werdegang. Das verwendete Foto muss im eingebundenen Ordner liegen und zum Bildpfad in der Markdown-Datei passen.

## Image weitergeben

Das gebaute Image als Datei speichern:

```bash
sudo docker image save \
  -o lebenslauf-generator-1.0.tar \
  lebenslauf-generator:1.0
```

Auf einem anderen Rechner mit Docker importieren:

```bash
sudo docker image load -i lebenslauf-generator-1.0.tar
```

Die Markdown-Datei und das Foto werden beim Containerstart eingebunden und sind nicht Bestandteil des Images.

## Was ich dabei umgesetzt habe

- Strukturierte Eingaben mit Python und PyYAML verarbeitet
- Die PDF-Erstellung über einen externen Compiler automatisiert
- Programm und Abhängigkeiten in einem Docker-Image bereitgestellt
- Eingabedateien über einen eingebundenen Ordner verarbeitet
- Den Build, die Verwendung und die Weitergabe dokumentiert

## Lizenz

Die Lizenzbedingungen stehen in der Datei `LICENSE`.

