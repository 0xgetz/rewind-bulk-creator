<div align="center">

<img src="../assets/logo.svg" alt="Rewind Bulk Creator" width="150" />

# Rewind Bulk Creator

**Crea cuentas de Rewind.ai en masa, verifícalas automáticamente y genera una clave API para cada una — con un solo comando.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-3DA639?style=flat-square)](../LICENSE)
[![Plataforma](https://img.shields.io/badge/Plataforma-Rewind.ai-6366F1?style=flat-square)](https://rewind.ai/)
[![Buzones](https://img.shields.io/badge/Buzones-mail.tm-06B6D4?style=flat-square)](https://mail.tm/)
[![Estado](https://img.shields.io/badge/Estado-Activo-22C55E?style=flat-square)]()

[English](../README.md) · [Español](README.es.md) · [Português](README.pt.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [中文](README.zh.md)

</div>

---

## Descripción general

Rewind Bulk Creator es una CLI de Python ligera que automatiza todo el flujo de
registro de Rewind.ai: crea buzones desechables en [mail.tm](https://mail.tm/),
registra una cuenta de Rewind.ai para cada uno, espera el correo de
verificación, sigue el enlace de verificación y por último crea una clave API
con un nombre aleatorio. Cada cuenta y clave se guardan en disco como JSON, CSV
y una lista simple `email:clave`.

Usa directamente los endpoints HTTP, así que no necesita navegador, ni driver
headless, ni Selenium.

## Funciones

- Un solo comando para crear cualquier cantidad de cuentas.
- Buzones desechables con mail.tm — sin configuración.
- Verificación de correo automática (lee el token del buzón).
- Nombres de clave API aleatorios y legibles (`key-cobalt-falcon-4f2a`).
- Contraseñas fuertes aleatorias o fijas con `--password`.
- Manejo elegante de límites de tasa con modo de espera y reintento.
- Salidas JSON, CSV y texto `email:clave` fáciles de canalizar.
- Modo de simulación (`--dry-run`) sin llamadas de red.

## Inicio rápido

```bash
git clone https://github.com/<tu-usuario>/rewind-bulk-creator.git
cd rewind-bulk-creator
pip install -r requirements.txt

# Crea 5 cuentas verificadas, cada una con su clave API
python rewind_bulk.py --count 5
```

Los resultados se guardan en `accounts/`:

```
accounts/
├── accounts.json
├── accounts.csv
└── keys.txt
```

## Uso

```bash
# Diez cuentas con buzones aleatorios de mail.tm
python rewind_bulk.py -n 10

# Tres cuentas con contraseña fija
python rewind_bulk.py -n 3 --password "MiClaveFija123!"

# Prefijo personalizado para los nombres de las claves
python rewind_bulk.py -n 5 --label-prefix worker

# Planificar sin llamadas de red
python rewind_bulk.py -n 3 --dry-run

# Continuar automáticamente cuando Rewind.ai limite tu IP
python rewind_bulk.py -n 20 --wait-on-rate-limit
```

## Cómo funciona

1. **Crea un buzón** en mail.tm.
2. **Se registra** con `POST /v1/auth/signup`.
3. **Espera el correo** de verificación y extrae el `token` del enlace.
4. **Verifica** con `POST /v1/auth/verify-email`.
5. **Crea una clave API** con `POST /v1/api-keys`.

## Requisitos

- Python 3.10 o superior
- `requests`
- Acceso de red a `api.mail.tm` y `api.rewind.ai`

## Notas y limitaciones

- Rewind.ai limita los registros por IP (por ejemplo, 10 por hora). La
  herramienta detecta el límite y se detiene limpiamente o espera.
- La entrega del correo depende de mail.tm; aumenta `--verify-timeout` si tarda.
- Úsalo con responsabilidad y respeta los términos de servicio de cada plataforma.

## Licencia

Publicado bajo la [Licencia MIT](../LICENSE).
