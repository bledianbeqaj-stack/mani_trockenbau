# Mani Trockenbau

Kompakte Python-Anwendung mit Streamlit-Webseite, SQLite-Terminbuchung, Preisberechnung, Pygame-Bauarbeiter-Runner und automatisierten Tests mit pytest.

## Projekt starten

**Wichtig:** Vor dem Start in den richtigen Projektordner wechseln.
In diesem Ordner müssen diese Dateien liegen:

* `app.py`
* `game.py`
* `requirements.txt`
* `README.md`

Prüfen mit:

```powershell
dir
```

## Start

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

Bedeutung der Befehle:

1. Virtuelle Umgebung erstellen
2. Virtuelle Umgebung aktivieren
3. Benötigte Pakete aus `requirements.txt` installieren
4. Streamlit-App starten

## Mini-Game direkt starten

```powershell
python game.py
```

## Tests starten

```powershell
python -m pytest
```

Die Tests prüfen Preisberechnung, Terminbuchung, Doppelbuchungsschutz, Eingabevalidierung und Zeitlogik.

## Hinweis zur Datenbank

Die Termine werden in einer SQLite-Datenbank gespeichert:

```text
data/appointments.db
```

Die Datei muss nicht manuell bearbeitet werden. Optional kann man sie mit einer SQLite-Viewer-Extension in VS Code anschauen.

## Hinweis

Falls `requirements.txt` nicht gefunden wird, befindet man sich sehr wahrscheinlich im falschen Ordner. Dann mit `dir` prüfen, ob `requirements.txt`, `app.py` und `game.py` im aktuellen Ordner liegen.

