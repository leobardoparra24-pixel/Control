"""Control de un televisor VIZIO SmartCast desde la red local.

Se ejecuta en una computadora conectada a la misma red Wi-Fi que el televisor.
Ejemplos:
    python vizio.py buscar
    python vizio.py emparejar --ip 192.168.1.50
    python vizio.py encender
    python vizio.py volumen subir 5
"""

import argparse
import asyncio
import json
import logging
import sys
import unicodedata
from pathlib import Path

from pyvizio import VizioAsync

CONFIG = Path(__file__).with_name("vizio_config.json")

# Nombres de modo de imagen a probar, en orden, para cada atajo
MODOS = {
    "peliculas": ["Calibrated Dark", "Calibrated", "Movie", "Cinema"],
    "juegos": ["Game"],
    "normal": ["Standard", "Calibrated", "Bright"],
}


def cargar_config():
    if not CONFIG.exists():
        sys.exit("Primero empareja el televisor: python vizio.py emparejar --ip <IP>")
    return json.loads(CONFIG.read_text())


def guardar_config(config):
    CONFIG.write_text(json.dumps(config, indent=2))


def tv(config=None):
    config = config or cargar_config()
    return VizioAsync("control", config["ip"], "TV", config.get("token", ""), "tv")


def mostrar(resultado, ok="Listo."):
    if resultado is None or resultado is False:
        sys.exit("El televisor no respondió. ¿Está encendido y en la misma red?")
    print(ok if resultado is True else resultado)


async def buscar(_):
    dispositivos = await asyncio.to_thread(VizioAsync.discovery_zeroconf, 5)
    if not dispositivos:
        print("No encontré televisores. Revisa que estés en la misma red Wi-Fi.")
    for d in dispositivos:
        print(f"{d.name}  modelo={d.model}  ip={d.ip}")


async def emparejar(args):
    aparato = tv({"ip": args.ip})
    inicio = await aparato.start_pair()
    if not inicio:
        sys.exit(f"No pude contactar al televisor en {args.ip}.")
    pin = input("Escribe el PIN que aparece en la pantalla del televisor: ").strip()
    respuesta = await aparato.pair(inicio.ch_type, inicio.token, pin)
    if not respuesta:
        sys.exit("PIN incorrecto o tiempo agotado. Intenta de nuevo.")
    config = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    config.update(ip=args.ip, token=respuesta.auth_token)
    guardar_config(config)
    print(f"Emparejado. Datos guardados en {CONFIG.name}.")


async def estado(_):
    aparato = tv()
    print("Modelo:  ", await aparato.get_model_name())
    print("Encendido:", "sí" if await aparato.get_power_state() else "no")
    print("Volumen: ", await aparato.get_current_volume())
    print("Silencio:", "sí" if await aparato.is_muted() else "no")
    print("Entrada: ", await aparato.get_current_input())
    print("App:     ", await aparato.get_current_app())


async def encender(_):
    mostrar(await tv().pow_on(), "Encendido.")


async def apagar(_):
    mostrar(await tv().pow_off(), "Apagado.")


async def volumen(args):
    aparato = tv()
    if args.accion == "subir":
        mostrar(await aparato.vol_up(args.pasos))
    elif args.accion == "bajar":
        mostrar(await aparato.vol_down(args.pasos))
    else:
        mostrar(await aparato.get_current_volume())


async def silencio(_):
    mostrar(await tv().mute_toggle())


async def entradas(_):
    lista = await tv().get_inputs_list()
    if not lista:
        mostrar(None)
    for entrada in lista:
        print(f"{entrada.name}  ({entrada.meta_name})")


async def entrada(args):
    mostrar(await tv().set_input(args.nombre), f"Entrada cambiada a {args.nombre}.")


async def apps(_):
    for nombre in sorted(await VizioAsync.get_apps_list()):
        print(nombre)


async def app(args):
    mostrar(await tv().launch_app(args.nombre), f"Abriendo {args.nombre}.")


async def tecla(args):
    aparato = tv()
    if not args.nombre:
        print("\n".join(sorted(aparato.get_remote_keys_list())))
        return
    mostrar(await aparato.remote(args.nombre.upper()))


async def streaming(args):
    config = cargar_config()
    if args.entrada:
        config["entrada_streaming"] = args.entrada
        guardar_config(config)
    if "entrada_streaming" not in config:
        entrada = input("En que entrada esta conectado el Google TV? (ej. HDMI-2): ").strip()
        if not entrada:
            sys.exit("No se indico ninguna entrada.")
        config["entrada_streaming"] = entrada.upper()
        guardar_config(config)
    entrada = config["entrada_streaming"]

    aparato = tv(config)
    if not await aparato.get_power_state():
        mostrar(await aparato.pow_on(), "Encendiendo...")
    # Recien encendido, el televisor tarda unos segundos en aceptar el cambio de entrada
    for _ in range(10):
        if await aparato.set_input(entrada, log_api_exception=False):
            print(f"Listo, en {entrada}.")
            return
        await asyncio.sleep(2)
    sys.exit(
        f"No pude cambiar a {entrada}. Revisa el nombre con 'python vizio.py entradas' "
        "y corrigelo con 'python vizio.py streaming --entrada <nombre>'."
    )


def elegir_modo(nombre, opciones):
    clave = unicodedata.normalize("NFKD", nombre.lower()).encode("ascii", "ignore").decode()
    candidatos = [c.lower() for c in MODOS.get(clave, [nombre])]
    for c in candidatos:
        for o in opciones:
            if o.lower() == c:
                return o
    for c in candidatos:
        for o in opciones:
            if c in o.lower():
                return o
    return None


async def modo(args):
    aparato = tv()
    opciones = await aparato.get_setting_options("picture", "picture_mode")
    if not isinstance(opciones, list) or not opciones:
        mostrar(None)
    if not args.nombre:
        print("Modo actual:", await aparato.get_setting("picture", "picture_mode"))
        print("Disponibles:", ", ".join(opciones))
        return
    elegido = elegir_modo(args.nombre, opciones)
    if not elegido:
        sys.exit(f"No encontre el modo '{args.nombre}'. Disponibles: {', '.join(opciones)}")
    mostrar(
        await aparato.set_setting("picture", "picture_mode", elegido),
        f"Modo de imagen: {elegido}.",
    )


async def ajustes(args):
    aparato = tv()
    if not args.tipo:
        mostrar("\n".join(await aparato.get_setting_types_list() or []) or None)
        return
    valores = await aparato.get_all_settings(args.tipo)
    if not valores:
        mostrar(None)
    for nombre, valor in valores.items():
        print(f"{nombre} = {valor}")


async def ajuste(args):
    valor = int(args.valor) if args.valor.lstrip("-").isdigit() else args.valor
    mostrar(await tv().set_setting(args.tipo, args.nombre, valor))


def main():
    parser = argparse.ArgumentParser(description="Control de televisor VIZIO SmartCast")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("buscar", help="buscar televisores en la red").set_defaults(func=buscar)

    p = sub.add_parser("emparejar", help="emparejar con el televisor (pide un PIN)")
    p.add_argument("--ip", required=True)
    p.set_defaults(func=emparejar)

    sub.add_parser("estado", help="ver estado actual").set_defaults(func=estado)
    sub.add_parser("encender").set_defaults(func=encender)
    sub.add_parser("apagar").set_defaults(func=apagar)

    p = sub.add_parser("volumen", help="ver, subir o bajar el volumen")
    p.add_argument("accion", nargs="?", choices=["subir", "bajar"])
    p.add_argument("pasos", nargs="?", type=int, default=1)
    p.set_defaults(func=volumen)

    sub.add_parser("silencio", help="activar/desactivar silencio").set_defaults(func=silencio)
    sub.add_parser("entradas", help="listar entradas (HDMI, etc.)").set_defaults(func=entradas)

    p = sub.add_parser("entrada", help="cambiar de entrada, ej. HDMI-1")
    p.add_argument("nombre")
    p.set_defaults(func=entrada)

    sub.add_parser("apps", help="listar apps disponibles").set_defaults(func=apps)

    p = sub.add_parser("app", help="abrir una app, ej. Netflix")
    p.add_argument("nombre")
    p.set_defaults(func=app)

    p = sub.add_parser("tecla", help="simular un botón del control remoto")
    p.add_argument("nombre", nargs="?", help="sin nombre muestra la lista de teclas")
    p.set_defaults(func=tecla)

    p = sub.add_parser("streaming", help="encender y cambiar a la entrada del Google TV")
    p.add_argument("--entrada", help="guardar la entrada a usar, ej. HDMI-2")
    p.set_defaults(func=streaming)

    p = sub.add_parser("modo", help="ver o cambiar modo de imagen (peliculas, juegos, normal)")
    p.add_argument("nombre", nargs="?")
    p.set_defaults(func=modo)

    p = sub.add_parser("ajustes", help="ver ajustes (sin tipo lista las categorías)")
    p.add_argument("tipo", nargs="?", help="ej. picture, audio")
    p.set_defaults(func=ajustes)

    p = sub.add_parser("ajuste", help="cambiar un ajuste, ej. picture brightness 40")
    p.add_argument("tipo")
    p.add_argument("nombre")
    p.add_argument("valor")
    p.set_defaults(func=ajuste)

    args = parser.parse_args()
    # Los fallos se informan con mensajes propios; se ocultan los de la libreria
    logging.getLogger("pyvizio").setLevel(logging.CRITICAL)
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
