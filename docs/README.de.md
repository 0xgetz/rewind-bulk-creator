<div align="center">

<img src="../assets/logo.svg" alt="Rewind Bulk Creator" width="150" />

# Rewind Bulk Creator

**Erstelle Rewind.ai-Konten in großen Mengen, verifiziere sie automatisch und erzeuge für jedes einen API-Schlüssel — mit einem einzigen Befehl.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-3DA639?style=flat-square)](../LICENSE)
[![Plattform](https://img.shields.io/badge/Plattform-Rewind.ai-6366F1?style=flat-square)](https://rewind.ai/)
[![Postfächer](https://img.shields.io/badge/Postf%C3%A4cher-mail.tm-06B6D4?style=flat-square)](https://mail.tm/)
[![Status](https://img.shields.io/badge/Status-Aktiv-22C55E?style=flat-square)]()

[English](../README.md) · [Español](README.es.md) · [Português](README.pt.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [中文](README.zh.md)

</div>

---

## Überblick

Rewind Bulk Creator ist ein schlankes Python-CLI, das den gesamten
Registrierungsablauf von Rewind.ai automatisiert: Es legt Wegwerf-Postfächer
bei [mail.tm](https://mail.tm/) an, registriert für jedes eine Rewind.ai-Konto,
wartet auf die Verifizierungs-E-Mail, ruft den Verifizierungslink auf und
erstellt schließlich einen zufällig benannten API-Schlüssel. Jedes Konto und
jeder Schlüssel werden als JSON, CSV und einfache `email:key`-Liste gespeichert.

Es spricht direkt mit den HTTP-Endpunkten — kein Browser, kein Headless-Treiber,
kein Selenium nötig.

## Funktionen

- Ein Befehl für beliebig viele Konten.
- Wegwerf-Postfächer über mail.tm — keine Konfiguration.
- Automatische E-Mail-Verifizierung (liest das Token aus dem Postfach).
- Zufällige, lesbare API-Schlüsselnamen (`key-cobalt-falcon-4f2a`).
- Zufällige starke Passwörter oder eigene mit `--password`.
- Sauberer Umgang mit Ratenlimits inklusive Warte- und Wiederholungsmodus.
- Ausgabe als JSON, CSV und `email:key`-Text.
- Dry-Run-Modus ohne Netzwerkanfragen.

## Schnellstart

```bash
git clone https://github.com/<dein-name>/rewind-bulk-creator.git
cd rewind-bulk-creator
pip install -r requirements.txt

# 5 verifizierte Konten, jeweils mit eigenem API-Schlüssel
python rewind_bulk.py --count 5
```

Ergebnisse landen in `accounts/`:

```
accounts/
├── accounts.json
├── accounts.csv
└── keys.txt
```

## Verwendung

```bash
# Zehn Konten mit zufälligen mail.tm-Postfächern
python rewind_bulk.py -n 10

# Drei Konten mit festem Passwort
python rewind_bulk.py -n 3 --password "MeinFestesPasswort123!"

# Eigener Präfix für die Schlüsselnamen
python rewind_bulk.py -n 5 --label-prefix worker

# Planen ohne Netzwerkanfragen
python rewind_bulk.py -n 3 --dry-run

# Automatisch fortfahren, wenn Rewind.ai die IP begrenzt
python rewind_bulk.py -n 20 --wait-on-rate-limit
```

## Wie es funktioniert

1. **Postfach anlegen** bei mail.tm.
2. **Registrieren** über `POST /v1/auth/signup`.
3. **Auf die E-Mail warten** und das `token` aus dem Link ziehen.
4. **Verifizieren** über `POST /v1/auth/verify-email`.
5. **API-Schlüssel erstellen** über `POST /v1/api-keys`.

## Voraussetzungen

- Python 3.10 oder neuer
- `requests`
- Netzwerkzugriff auf `api.mail.tm` und `api.rewind.ai`

## Hinweise und Grenzen

- Rewind.ai begrenzt Registrierungen pro IP (z. B. 10 pro Stunde). Das Tool
  erkennt das Limit und stoppt sauber oder wartet.
- Die Zustellung hängt von mail.tm ab; erhöhe `--verify-timeout` bei Verzögerung.
- Bitte verantwortungsvoll nutzen und die Nutzungsbedingungen der Plattform
  beachten.

## Lizenz

Veröffentlicht unter der [MIT-Lizenz](../LICENSE).
