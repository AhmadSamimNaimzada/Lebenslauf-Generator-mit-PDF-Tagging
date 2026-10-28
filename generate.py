"""Lebenslauf aus einer Markdown-Datei als getaggtes PDF erstellen."""

import argparse
from pathlib import Path
import shutil
import subprocess

import re

import yaml


def parse_frontmatter(content: str) -> tuple[dict, str]:
    content = content.lstrip("\ufeff").strip()
    if not re.match(r"^---[ \t]*(?:\r?\n|$)", content):
        return {}, content
    match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)(.*)$", content, re.S)
    if not match:
        raise ValueError("Der YAML-Kopf muss mit einer eigenen --- Zeile enden.")
    try:
        data = yaml.safe_load(match[1])
    except yaml.YAMLError as error:
        raise ValueError(f"Ungültiger YAML-Kopf: {error}") from error
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("Der YAML-Kopf muss Schlüssel und Werte enthalten.")
    return data, match[2].strip()


def escape_latex(text: object) -> str:
    """Escape text once, rather than treating Markdown input as TeX commands."""
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
                    "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
                    "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in str(text if text is not None else ""))


def format_inline(text: object) -> str:
    """Support **bold** and *italic*; other Markdown stays escaped text."""
    chunks = re.split(r"(\*\*[^*\n]+\*\*|(?<!\*)\*[^*\n]+\*(?!\*))", str(text))
    result = []
    for chunk in chunks:
        if chunk.startswith("**") and chunk.endswith("**") and len(chunk) > 4:
            result.append(r"\textbf{" + escape_latex(chunk[2:-2]) + "}")
        elif chunk.startswith("*") and chunk.endswith("*") and len(chunk) > 2:
            result.append(r"\emph{" + escape_latex(chunk[1:-1]) + "}")
        else:
            result.append(escape_latex(chunk))
    return "".join(result)


def parse_cv_body(body: str) -> dict:
    """Parse # sections and ### title | period entries in their original order."""
    sections = {}
    current_section = None
    current_item = None
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("# "):
            current_section = line[2:].strip()
            sections.setdefault(current_section, [])
            current_item = None
        elif line.startswith("### ") and current_section:
            title, _, period = line[4:].partition("|")
            current_item = {"title": title.strip(), "time": period.strip(), "place": "", "desc": ""}
            sections[current_section].append(current_item)
        elif current_item is not None:
            if line and not current_item["place"]:
                current_item["place"] = line
            elif current_item["place"]:
                current_item["desc"] += ("\n" if current_item["desc"] else "") + line
    return sections


DEFAULTS = {
    'primary_color': '005580', 'subtext_color': '555555',
    'font_family': 'Latin Modern Sans', 'font_size': '11pt',
    'margin': '12mm',
    'photo_position': 'none', 'photo_width': '3.2cm',
}


def load_design(base_dir: Path | None = None, custom_design: dict | None = None) -> dict:
    design = dict(DEFAULTS)
    if custom_design is not None:
        if not isinstance(custom_design, dict):
            raise ValueError('Design-Optionen müssen ein Wörterbuch sein.')
        design.update(custom_design)
    unknown = set(design) - set(DEFAULTS)
    if unknown:
        raise ValueError('Unbekannte Design-Optionen: ' + ', '.join(sorted(unknown)))
    for key in ('primary_color', 'subtext_color'):
        value = str(design[key]).lstrip('#')
        if not re.fullmatch(r'[0-9a-fA-F]{6}', value):
            raise ValueError(f'{key}: sechs hexadezimale Zeichen erwartet.')
        design[key] = value
    for key in ('font_size',):
        if design[key] not in ('10pt', '11pt', '12pt'):
            raise ValueError(f'{key}: 10pt, 11pt oder 12pt erwartet.')
    if not re.fullmatch(r'[\w .-]+', str(design['font_family'])):
        raise ValueError('font_family enthält ungültige Zeichen.')
    for key in ('margin', 'photo_width'):
        if not re.fullmatch(r'(?:\d+(?:\.\d+)?)(?:mm|cm|pt)', str(design[key])):
            raise ValueError(f'{key}: eine positive Länge wie 12mm erwartet.')
        if float(re.match(r'[\d.]+', str(design[key]))[0]) <= 0:
            raise ValueError(f'{key} muss größer als null sein.')
    if design['photo_position'] not in ('none', 'left', 'right'):
        raise ValueError('photo_position: none, left oder right erwartet.')
    return design


def format_education_desc(desc: str) -> str:
    """Erhält Absätze und wandelt Markdown-Stichpunkte in LaTeX-Listen um."""
    parts = []
    prose = []
    bullets = []

    def add_prose():
        if prose:
            parts.append("\\noindent " + " ".join(format_inline(line) for line in prose) + "\\par")
            prose.clear()

    def add_bullets():
        if bullets:
            items = "\n".join(f"    \\item {format_inline(line)}" for line in bullets)
            # Native Listenparameter; kein zusätzliches enumitem-Paket.
            parts.append(
                "\\begin{itemize}[left-margin=1.1em, label-sep=0.35em, "
                "label-width=0.75em, item-vspace=1pt, "
                "begin-vspace=2pt, end-vspace=2pt, "
                "begin-extra-vspace=0pt, end-extra-vspace=0pt, "
                "para-vspace=0pt]\n"
                f"{items}\n"
                "\\end{itemize}"
            )
            bullets.clear()

    for raw_line in desc.splitlines():
        line = raw_line.strip()
        if not line:
            add_prose()
            add_bullets()
        elif line.startswith(("- ", "* ", "• ")):
            add_prose()
            bullets.append(line[2:].strip())
        else:
            add_bullets()
            prose.append(line)

    add_prose()
    add_bullets()

    # Explizite Absatzenden statt leerer LaTeX-Absätze zwischen den Blöcken.
    return "\n%\n".join(parts)


def build_cv_latex(
    data: dict, body: str, base_dir: Path, custom_design: dict | None = None
) -> str:
    design = load_design(base_dir, custom_design if custom_design is not None else data.get("design", {}))
    for key in ("kontakt", "it_kenntnisse", "sprachen"):
        if not isinstance(data.get(key, {}), dict):
            raise ValueError(f"{key} muss Schlüssel und Werte enthalten.")
    name = escape_latex(data.get("name", "Alex Beispiel"))
    titel = format_inline(data.get("titel", ""))
    profil = format_inline(data.get("profil", ""))
    foto_raw = data.get("foto", "")
    text_header = r"""\raggedright
    {\Huge\bfseries\color{cvblue} #2}\par\vspace{0.4ex}
    {\large\bfseries\color{subtext} #3}\par\vspace{1ex}
    {\small #4}\par"""
    header_code = text_header
    if design["photo_position"] != "none":
        if not foto_raw:
            raise ValueError("Für ein Foto bitte 'foto' im Lebenslauf angeben oder photo_position auf none setzen.")
        photo = (base_dir / str(foto_raw)).resolve()
        if not photo.is_file() or photo.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            raise ValueError("Das angegebene Foto muss eine vorhandene JPG- oder PNG-Datei sein.")
        if any(c in photo.as_posix() for c in "{}%#\n\r"):
            raise ValueError("Der Fotopfad enthält ungeeignete Zeichen.")
        image = r"\includegraphics[width=" + design["photo_width"] + r",alt={Porträtfoto}]{\detokenize{" + photo.as_posix() + "}}"
        text_block = r"\begin{minipage}[t]{0.73\textwidth}\vspace{0pt}" + text_header + r"\end{minipage}"
        image_block = r"\begin{minipage}[t]{0.25\textwidth}\vspace{0pt}" + image + r"\end{minipage}"
        header_code = (image_block + r"\hfill" + text_block if design["photo_position"] == "left"
                       else text_block + r"\hfill" + image_block)


    # Kontakt
    kontakt = data.get("kontakt", {})
    kontakt_items = []
    for k, v in kontakt.items():
        k_clean = escape_latex(str(k).rstrip(":"))
        v = escape_latex(v)
        if k_clean.lower() == "geburt":
            k_clean = "Geboren"
        if "mail" in str(k).lower():
            kontakt_items.append(
                f"    \\kitem{{{k_clean}:}}{{\\href{{mailto:{v}}}{{\\small {v}}}}}"
            )
        elif k_clean.lower() == "adresse":
            val = v
            if ", " in val and "\\newline" not in val and "\\\\" not in val:
                val = val.replace(", ", ",\\newline ")
            kontakt_items.append(f"    \\kitem{{{k_clean}:}}{{\\small {val}}}")
        else:
            kontakt_items.append(
                f"    \\kitem{{{k_clean}:}}{{\\small {v}}}"
            )
    kontakt_str = "\n".join(kontakt_items)

    # IT-Kenntnisse
    it = data.get("it_kenntnisse", {})
    it_items = [f"    \\ititem{{{escape_latex(k)}}}{{{format_inline(v)}}}" for k, v in it.items()]
    it_str = "\n".join(it_items)

    # Sprachen
    sprachen = data.get("sprachen", {})
    sprachen_items = [
        f"    \\langitem{{{escape_latex(k)}}}{{{escape_latex(v)}}}" for k, v in sprachen.items()
    ]
    sprachen_str = "\n".join(sprachen_items)

    # Abschnitte
    sections = parse_cv_body(body)

    # Ausbildung
    ausbildung_items = [
        f"    \\eduitem{{{format_inline(item.get('title', ''))}}}\n"
        f"            {{{escape_latex(item.get('time', ''))}}}\n"
        f"            {{{format_inline(item.get('place', ''))}}}\n"
        f"            {{{format_education_desc(item.get('desc', ''))}}}"
        for item in sections.get("Ausbildung", [])
    ]
    ausbildung_str = "\n    %\n".join(ausbildung_items)

    # Berufserfahrung
    beruf_items = [
        f"    \\jobitem{{{format_inline(item.get('title', ''))}}}\n"
        f"            {{{escape_latex(item.get('time', ''))}}}\n"
        f"            {{{format_inline(item.get('place', ''))}}}\n"
        f"            {{{format_education_desc(item.get('desc', ''))}}}"
        for item in sections.get("Berufserfahrung", [])
    ]
    beruf_str = "\n    %\n".join(beruf_items)

    extra_sections = []
    for heading, items in sections.items():
        if heading in {"Ausbildung", "Berufserfahrung"}:
            continue
        entries = []
        for item in items:
            entries.append(r"\eduitem{" + format_inline(item["title"]) + "}{" + escape_latex(item["time"]) + "}{" + format_inline(item["place"]) + "}{" + format_education_desc(item["desc"]) + "}")
        extra_sections.append(r"\cvsection{" + escape_latex(heading) + "}\n" + "\n".join(entries))
    extra_str = "\n".join(extra_sections)
    tex = f"""% !TeX spellcheck = de_DE
% !TeX program = lualatex

\\DocumentMetadata{{
  lang=de-DE,
  pdfstandard=ua-2,
  tagging = on,
  pdfversion=2.0,
  testphase={{phase-III}}
}}

\\documentclass[{design["font_size"]},a4paper]{{article}}

\\usepackage{{fontspec}}              
\\usepackage[ngerman]{{babel}}
\\usepackage[margin={design["margin"]}]{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{xcolor}}
\\usepackage{{hyperref}}

\\AssignTaggingSocketPlug{{para/semantic/begin}}{{noop}}
\\AssignTaggingSocketPlug{{para/semantic/end}}{{noop}}

\\setmainfont{{{design["font_family"]}}}
\\setsansfont{{{design["font_family"]}}}
\\renewcommand{{\\familydefault}}{{\\sfdefault}}

% Typografische Farbdefinitionen
\\definecolor{{cvblue}}{{HTML}}{{{design["primary_color"]}}}
\\definecolor{{subtext}}{{HTML}}{{{design["subtext_color"]}}}

\\tagpdfsetup{{
  math/mathml/luamml/load=false,
  add-new-tag = Zeit/Span,
  add-new-tag = Ausbildungsort/Em,
  add-new-tag = Arbeitgeber/Em,
  add-new-tag = Ziel/Div,
  add-new-tag = Kategorie/Span,
  add-new-tag = Kenntnisse/Span,
  add-new-tag = Sprache/Span,
  add-new-tag = Niveau/Span,
  add-new-tag = KontaktLabel/Span,
  add-new-tag = KontaktWert/Span
}}

\\setcounter{{secnumdepth}}{{0}}

\\newcommand{{\\tagtext}}[2]{{%
  \\tagstructbegin{{tag=#1}}%
  \\tagmcbegin{{tag=#1}}%
  #2%
  \\tagmcend%
  \\tagstructend%
}}

% Beschreibungen enthalten Absätze und Listen. Kein Inline-MC um den Block!
% Die Rolle Ziel bleibt erhalten und wird auf den Blocktyp Div abgebildet.
\\newcommand{{\\tagblock}}[2]{{%
  \\tagstructbegin{{tag=#1}}%
  #2\\par%
  \\tagstructend%
}}

\\makeatletter
\\renewcommand\\section{{\\@startsection{{section}}{{1}}{{\\z@}}%
                               {{-0.2ex}}%
                               {{0.1ex}}%
                               {{\\normalfont\\Large\\bfseries\\color{{cvblue}}\\scshape}}}}
\\makeatother

\\newcommand{{\\cvsection}}[1]{{%
  \\section{{#1}}%
  \\vspace*{{-0.6ex}}%
  \\tagpdfparaOff
  \\noindent{{\\color{{cvblue}}\\rule{{\\linewidth}}{{0.8pt}}}}\\par
  \\vspace*{{0.4ex}}%
  \\tagpdfparaOn
}}

% Foto ist optional; ohne Foto nutzt die Kopfzeile die ganze Breite.
\\newcommand{{\\cvheader}}[4]{{%
  {header_code}
  \\vspace{{1ex}}%
}}

% Linke Spalte (Sidebar)
\\newenvironment{{kontakt}}{{\\cvsection{{Kontakt}}}}{{}}
\\newlength{{\\kontaktlabelwidth}}
\\setlength{{\\kontaktlabelwidth}}{{1.85cm}}
\\newcommand{{\\kitem}}[2]{{%
  \\noindent\\hangindent=\\kontaktlabelwidth\\hangafter=1%
  \\makebox[\\kontaktlabelwidth][l]{{\\tagtext{{KontaktLabel}}{{\\textbf{{#1}}}}}}%
  \\tagtext{{KontaktWert}}{{#2}}\\par\\vspace{{0.4ex}}%
}}

\\newenvironment{{itkenntnisse}}{{\\cvsection{{IT-Kenntnisse}}}}{{}}
\\newcommand{{\\ititem}}[2]{{%
  \\noindent\\tagtext{{Kategorie}}{{\\textbf{{#1}}}}\\newline
  {{\\small \\tagtext{{Kenntnisse}}{{#2}}}}\\par\\vspace{{0.5ex}}%
}}

\\newenvironment{{sprachen}}{{\\cvsection{{Sprachen}}}}{{}}
\\newcommand{{\\langitem}}[2]{{%
  \\noindent\\tagtext{{Sprache}}{{\\textbf{{#1}}}} (\\tagtext{{Niveau}}{{#2}})\\par\\vspace{{0.4ex}}%
}}

% Rechte Spalte (Werdegang)
\\newenvironment{{ausbildung}}{{\\cvsection{{Ausbildung}}}}{{}}
\\newcommand{{\\eduitem}}[4]{{%
  \\noindent\\textbf{{#1}}%
  \\hfill {{\\small\\color{{subtext}}\\mbox{{\\tagtext{{Zeit}}{{#2}}}}}}\\newline
  {{\\color{{subtext}}\\tagtext{{Ausbildungsort}}{{#3}}}}\\par%
  \\ifx&#4&\\else
    {{\\small\\tagblock{{Ziel}}{{#4}}}}%
  \\fi
  \\vspace{{1ex}}%
}}

\\newenvironment{{berufserfahrung}}{{\\cvsection{{Berufserfahrung}}}}{{}}
\\newcommand{{\\jobitem}}[4]{{%
  \\noindent\\textbf{{#1}}%
  \\hfill {{\\small\\color{{subtext}}\\mbox{{\\tagtext{{Zeit}}{{#2}}}}}}\\newline
  {{\\color{{subtext}}\\tagtext{{Arbeitgeber}}{{#3}}}}\\par%
  \\ifx&#4&\\else
    {{\\small\\tagblock{{Ziel}}{{#4}}}}%
  \\fi
  \\vspace{{1ex}}%
}}

\\hypersetup{{
  colorlinks = true, 
  urlcolor = cvblue, 
  linkcolor = cvblue,
  pdftitle={{Lebenslauf {name}}},
  pdfauthor={{{name}}}
}}

\\begin{{document}}
\\setlength{{\\topskip}}{{0pt}}
\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{0pt}}
\\pagestyle{{empty}}

% Header
\\cvheader{{}}
         {{{name}}}
         {{{titel}}}
         {{{profil}}}

% Layout-Raster
\\begin{{minipage}}[t]{{0.33\\textwidth}}
\\raggedright

  \\begin{{kontakt}}
{kontakt_str}
  \\end{{kontakt}}%
  \\vspace{{0.3em}}%
  %
  \\begin{{itkenntnisse}}
{it_str}
  \\end{{itkenntnisse}}%
  \\vspace{{0.3em}}%
  %
  \\begin{{sprachen}}
{sprachen_str}
  \\end{{sprachen}}%
  %
\\tagpdfsetup{{sec/end=-10}}%
\\end{{minipage}}%
\\hfill
\\begin{{minipage}}[t]{{0.64\\textwidth}}
\\raggedright

  \\begin{{ausbildung}}
{ausbildung_str}
  \\end{{ausbildung}}%
  \\vspace{{0.3em}}%
  %
  \\begin{{berufserfahrung}}
{beruf_str}
  \\end{{berufserfahrung}}%
{extra_str}
  %
\\tagpdfsetup{{sec/end=-10}}%
\\end{{minipage}}

\\end{{document}}
"""
    return tex


def _report_compiler_error(output: str) -> None:
    lines = output.splitlines()
    useful = [line for line in lines if line.startswith("!") or "Error" in line]
    for line in (useful[:5] or lines[-6:]):
        print(f"  {line}")


def compile_latex(tex_path: Path) -> bool:
    """Run two LuaLaTeX passes; a failed pass never counts as a PDF build."""
    tex_path = Path(tex_path).resolve()
    pdf_path = tex_path.with_suffix(".pdf")
    try:
        # A previous build must not be mistaken for the current result.
        pdf_path.unlink(missing_ok=True)
    except OSError as exc:
        print(f"Fehler: Alte PDF kann nicht entfernt werden: {exc}")
        return False

    executable = shutil.which("lualatex")
    if not executable:
        print("Fehler: LuaLaTeX wurde nicht gefunden. Installiere eine TeX-Distribution "
              "mit LuaLaTeX oder verwende --tex-only.")
        return False
    command = [
        executable,
        "--no-shell-escape",
        "-halt-on-error",
        "-interaction=nonstopmode",
        tex_path.name,
    ]
    try:
        for pass_number in (1, 2):
            result = subprocess.run(
                command,
                cwd=tex_path.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
            )
            if result.returncode != 0:
                print(f"Fehler: LuaLaTeX-Durchlauf {pass_number} für {tex_path.name} fehlgeschlagen.")
                _report_compiler_error(result.stdout or "")
                pdf_path.unlink(missing_ok=True)
                return False
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Fehler beim Aufruf von LuaLaTeX: {exc}")
        try:
            pdf_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False

    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        print(f"Fehler: LuaLaTeX hat keine PDF erstellt: {pdf_path.name}")
        return False
    for suffix in (".aux", ".log", ".out", ".toc", ".synctex.gz"):
        try:
            (tex_path.parent / f"{tex_path.stem}{suffix}").unlink(missing_ok=True)
        except OSError:
            pass
    print(f"PDF erstellt: {pdf_path}")
    return True



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path,
                        default=Path(__file__).resolve().parent / "lebenslauf.md",
                        help="Lebenslauf-Markdown (Standard: lebenslauf.md neben diesem Skript)")
    parser.add_argument("--output", type=Path,
                        help="Ausgabeordner (Standard: Ordner der Markdown-Datei)")
    parser.add_argument("--tex-only", action="store_true", help="Nur LaTeX erzeugen")
    args = parser.parse_args(argv)
    source = args.source.resolve()
    output = (args.output or source.parent).resolve()
    try:
        if source.suffix.lower() != ".md":
            raise ValueError("Als Eingabe wird eine Markdown-Datei (.md) erwartet.")
        data, body = parse_frontmatter(source.read_text(encoding="utf-8-sig"))
        if not data.get("name"):
            raise ValueError("Bitte im YAML-Kopf einen Namen angeben.")
        tex = build_cv_latex(data, body, source.parent)
        output.mkdir(parents=True, exist_ok=True)
        tex_path = output / (source.stem + ".tex")
        tex_path.write_text(tex, encoding="utf-8")
        print(f"LaTeX erstellt: {tex_path}")
        return 0 if args.tex_only or compile_latex(tex_path) else 1
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"Fehler: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
