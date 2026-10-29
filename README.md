# Lebenslauf-Generator mit PDF-Tagging

Eine Datei `lebenslauf.md` enthält alle Inhalte, Kontaktdaten und Layout-Einstellungen. `generate.py` erstellt daraus `lebenslauf.tex` und `lebenslauf.pdf` mit strukturierten PDF-Tags.

## Start

Benötigt werden Python ab 3.11 und eine aktuelle TeX-Installation mit LuaLaTeX, LaTeX ab Juni 2026, den Paketen `fontspec`, `babel` (Deutsch), `geometry`, `graphicx`, `xcolor`, `hyperref` und PDF-Tagging-Unterstützung. Die Standardschrift ist Latin Modern Sans.

Im Projektordner ausführen:

```sh
python -m pip install -r requirements.txt
python generate.py
```

Danach liegen `lebenslauf.pdf` und die zugehörige LaTeX-Datei neben `lebenslauf.md`.

Optional: einen anderen Eingabepfad oder Ausgabeordner verwenden oder nur die LaTeX-Datei erzeugen:

```sh
python generate.py lebenslauf.md --output output
python generate.py --tex-only
```

## Bearbeiten

- Im YAML-Kopf stehen Name, Kontakt, Kenntnisse, Sprachen und `design`.
- `# Abschnitt` beginnt einen Bereich, `### Titel | Zeitraum` einen Eintrag.
- Die erste Zeile unter einem Eintrag enthält Institution oder Ort, danach folgt die Beschreibung.
- `- Stichpunkt`, `**fett**` und `*kursiv*` werden unterstützt. LaTeX-Sonderzeichen werden maskiert.
- Ein Foto ist optional: `foto: "profilfoto.jpg"` im YAML-Kopf ergänzen und `design.photo_position` auf `left` oder `right` setzen. Standardmäßig wird kein Foto benötigt.

Die Beispieldaten sind vollständig fiktiv. Eigene Kontaktdaten oder Fotos vor einer Veröffentlichung entfernen. Generierte Dokumente sind in `.gitignore` ausgeschlossen.

Das zweispaltige Layout ist für kurze Lebensläufe ausgelegt; die Spalten brechen nicht automatisch auf weitere Seiten um. PDF-Tags sind keine Garantie für PDF/UA-Konformität oder eine bestimmte ATS-Auswertung. Nur vertrauenswürdige lokale Eingaben verwenden.

MIT-Lizenz, siehe [LICENSE](LICENSE).
