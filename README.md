# Control de televisor VIZIO

Programa para controlar un televisor VIZIO SmartCast desde la computadora,
usando la misma conexión local que usa la app VIZIO.

**Importante:** la computadora debe estar conectada a la misma red Wi-Fi que el televisor.

## Instalación (una sola vez)

1. Instala Python 3.10 o más reciente: https://www.python.org/downloads/
   (en Windows marca la casilla **Add Python to PATH**).
2. Descarga este repositorio (botón verde **Code** → **Download ZIP**) y descomprímelo.
3. Abre una terminal en esa carpeta y ejecuta:

```bash
pip install -r requirements.txt
```

## Forma fácil en Windows: `Iniciar.bat`

Haz doble clic en **Iniciar.bat**. La primera vez instala lo necesario y te pide la IP del
televisor para emparejar (escribe el PIN que aparece en la pantalla). Después muestra un menú
con números para encender, apagar, cambiar volumen, entrada, abrir apps, etc.

Si Windows muestra "Windows protegió su PC", toca **Más información → Ejecutar de todas formas**.

## Primer uso: emparejar

1. Enciende el televisor.
2. Busca su dirección IP:

```bash
python vizio.py buscar
```

   Si no aparece, búscala en el televisor: **Menú → Red → Información de red**.

3. Empareja (cambia la IP por la tuya):

```bash
python vizio.py emparejar --ip 192.168.1.50
```

   El televisor mostrará un PIN; escríbelo en la terminal. Los datos se guardan en
   `vizio_config.json` (no lo compartas: permite controlar tu televisor).

## Comandos

| Comando | Qué hace |
|---|---|
| `python vizio.py estado` | Muestra modelo, encendido, volumen, entrada y app |
| `python vizio.py encender` / `apagar` | Enciende o apaga |
| `python vizio.py volumen` | Muestra el volumen |
| `python vizio.py volumen subir 5` | Sube 5 niveles (`bajar` para bajar) |
| `python vizio.py silencio` | Activa o quita el silencio |
| `python vizio.py entradas` | Lista las entradas (HDMI, etc.) |
| `python vizio.py entrada HDMI-1` | Cambia de entrada |
| `python vizio.py apps` | Lista las apps conocidas |
| `python vizio.py app Netflix` | Abre una app |
| `python vizio.py tecla` | Lista los botones del control remoto |
| `python vizio.py tecla HOME` | Presiona un botón (HOME, OK, UP, BACK...) |
| `python vizio.py ajustes` | Lista categorías de ajustes |
| `python vizio.py ajustes picture` | Muestra los ajustes de imagen |
| `python vizio.py ajuste picture brightness 40` | Cambia un ajuste |

Los nombres de ajustes varían según el modelo; usa `ajustes <categoría>` para ver los de tu televisor.
