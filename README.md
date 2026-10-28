# Lebenslauf-Generator mit PDF-Tagging

Alle Inhalte und Einstellungen stehen in `lebenslauf.md`. Der Generator erstellt daraus `lebenslauf.tex` und `lebenslauf.pdf` mit strukturierten PDF-Tags.

## Was muss installiert sein?

- **Python ab 3.11**
- **PyYAML ab 6.0.3, kleiner als 7.0** zum Lesen der YAML-Kopfdaten
- **LuaLaTeX mit LaTeX ab 2026-06-01** und aktueller PDF-Tagging-Unterstützung
- **Latin Modern Sans**, oder eine andere installierte Schrift in `design.font_family`

Die TeX-Vorlage benötigt außerdem `fontspec`, `babel` mit Deutsch, `geometry`, `graphicx`, `xcolor`, `hyperref` und `tagpdf`. Die TeX-Live-Paketsammlungen unten bringen diese Bestandteile und die Tagging-Infrastruktur mit.

## Ubuntu 26.04: Python und PyYAML installieren

```bash
sudo apt update
sudo apt install python3 python3-yaml curl perl ca-certificates
```

Unter Ubuntu 26.04 liefert `python3-yaml` die benötigte PyYAML-Version. Die Installation erfolgt direkt über Ubuntu-Pakete; pip ist dafür nicht erforderlich. Die folgenden Befehle verwenden ausdrücklich das System-Python unter `/usr/bin/python3`.

## Ubuntu: LuaLaTeX installieren

Für diese Vorlage wird LaTeX ab Juni 2026 benötigt. Die TeX-Pakete älterer Distributionsstände reichen dafür nicht aus. Die folgenden Befehle installieren aktuelles TeX Live im eigenen Benutzerordner, ohne es als root auszuführen:

```bash
mkdir -p ~/texlive-install
cd ~/texlive-install
curl -fL -o install-tl-unx.tar.gz https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
tar -xzf install-tl-unx.tar.gz
cd install-tl-20*
perl ./install-tl --no-interaction --scheme=small --no-doc-install --no-src-install --texdir="$HOME/texlive"

export PATH="$HOME/texlive/bin/x86_64-linux:$PATH"
tlmgr install collection-luatex collection-latexextra collection-langgerman collection-fontsrecommended
```

Die Installation kann einige Zeit dauern. Der gezeigte Binärpfad gilt für Linux x86_64. Bei einer anderen Architektur den vom Installer angegebenen Pfad verwenden. `collection-luatex` installiert die LuaTeX-/LuaLaTeX-Unterstützung.

Damit neue Bash-Terminals die Programme ebenfalls finden, einmalig ausführen:

```bash
echo 'export PATH="$HOME/texlive/bin/x86_64-linux:$PATH"' >> ~/.bashrc
```

## Lebenslauf erstellen

Nach der Installation wieder in den heruntergeladenen Projektordner wechseln. Dort ausführen:

```bash
/usr/bin/python3 generate.py --check
/usr/bin/python3 generate.py
```

`--check` zeigt fehlende oder veraltete Voraussetzungen an. Die PDF und die LaTeX-Datei werden neben `lebenslauf.md` gespeichert.

Nur LaTeX erstellen, ohne PDF-Kompilierung:

```bash
/usr/bin/python3 generate.py --tex-only
```

Anderen Ausgabeordner verwenden:

```bash
/usr/bin/python3 generate.py lebenslauf.md --output output
```

## Windows

Python ab 3.11 und eine aktuelle TeX-Live- oder MiKTeX-Installation mit LuaLaTeX und LaTeX ab 2026-06-01 installieren. Nach der TeX-Installation das Terminal neu öffnen. Im Projektordner ausführen:

```powershell
py -3 -m pip install -r requirements.txt
py -3 generate.py --check
py -3 generate.py
```

`requirements.txt` enthält nur die Python-Abhängigkeit PyYAML. LuaLaTeX wird separat installiert.

## Lebenslauf und Foto bearbeiten

- YAML-Kopf: Name, Kontakt, Kenntnisse, Sprachen und `design`.
- `# Abschnitt` beginnt einen Bereich, `### Titel | Zeitraum` einen Eintrag.
- Die erste Zeile unter einem Eintrag enthält Institution oder Ort, danach folgt die Beschreibung.
- `- Stichpunkt`, `**fett**` und `*kursiv*` werden unterstützt; LaTeX-Sonderzeichen werden maskiert.

Für ein Foto im YAML-Kopf auf oberster Ebene `foto: "profilfoto.jpg"` ergänzen. In der vorhandenen `design`-Gruppe `photo_position: "left"` oder `"right"` einstellen. `"none"` schaltet das Foto aus. Der Fotopfad ist relativ zur Markdown-Datei. Das veröffentlichte Beispiel benötigt kein Foto.

Die Beispieldaten sind vollständig fiktiv. Eigene Kontaktdaten oder Fotos vor einer Veröffentlichung entfernen. Generierte Dokumente sind in `.gitignore` ausgeschlossen.

Das zweispaltige Layout ist für kurze Lebensläufe ausgelegt; die Spalten brechen nicht automatisch auf weitere Seiten um. PDF-Tags sind keine Garantie für PDF/UA-Konformität oder eine bestimmte ATS-Auswertung. Nur vertrauenswürdige lokale Eingaben verwenden.

MIT-Lizenz, siehe [LICENSE](LICENSE).
