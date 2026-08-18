import argparse
import datetime
import json
import os
import pathlib
import sys
import unicodedata


RUTA_POR_DEFECTO = pathlib.Path(
    os.environ.get(
        "NOTAS_CLI_FILE",
        pathlib.Path.home() / ".notas-cli" / "notas.json",
    )
)


def _resolver_ruta(ruta=None):
    """Devuelve la ruta indicada o la ruta de almacenamiento por defecto."""
    return pathlib.Path(ruta) if ruta is not None else RUTA_POR_DEFECTO


def cargar_notas(ruta=None) -> list[dict]:
    """Carga y devuelve las notas guardadas en un archivo JSON."""
    archivo = _resolver_ruta(ruta)
    if not archivo.exists():
        return []

    try:
        with archivo.open("r", encoding="utf-8") as fichero:
            return json.load(fichero)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"El archivo de notas '{archivo}' contiene JSON corrupto: {error.msg}."
        ) from error


def guardar_notas(ruta, notas: list[dict]) -> None:
    """Guarda las notas como JSON y crea los directorios necesarios."""
    archivo = _resolver_ruta(ruta)
    archivo.parent.mkdir(parents=True, exist_ok=True)

    with archivo.open("w", encoding="utf-8") as fichero:
        json.dump(notas, fichero, indent=2, ensure_ascii=False)


def siguiente_id(notas: list[dict]) -> int:
    """Calcula el siguiente identificador disponible para una lista de notas."""
    return max((nota["id"] for nota in notas), default=0) + 1


def agregar_nota(ruta, texto, etiquetas=None) -> dict:
    """Crea una nota, la persiste y devuelve la nota creada."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("El texto de la nota no puede estar vacio.")

    notas = cargar_notas(ruta)
    nota = {
        "id": siguiente_id(notas),
        "texto": texto,
        "etiquetas": list(etiquetas) if etiquetas is not None else [],
        "creada_en": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    notas.append(nota)
    guardar_notas(ruta, notas)
    return nota


def listar_notas(ruta) -> list[dict]:
    """Devuelve las notas ordenadas por identificador ascendente."""
    return sorted(cargar_notas(ruta), key=lambda nota: nota["id"])


def _plegar_texto(valor) -> str:
    """Normaliza texto para compararlo sin mayusculas, minusculas ni acentos."""
    normalizado = unicodedata.normalize("NFD", str(valor))
    return "".join(
        caracter
        for caracter in normalizado
        if unicodedata.category(caracter) != "Mn"
    ).casefold()


def buscar_notas(ruta, consulta) -> list[dict]:
    """Busca una coincidencia parcial en el texto y las etiquetas de las notas."""
    consulta_normalizada = _plegar_texto(consulta)
    resultados = []

    for nota in listar_notas(ruta):
        campos = [nota.get("texto", ""), *nota.get("etiquetas", [])]
        if any(consulta_normalizada in _plegar_texto(campo) for campo in campos):
            resultados.append(nota)

    return resultados


def borrar_nota(ruta, nota_id) -> bool:
    """Elimina y persiste la nota indicada; informa si fue encontrada."""
    notas = cargar_notas(ruta)
    notas_restantes = [nota for nota in notas if nota.get("id") != nota_id]

    if len(notas_restantes) == len(notas):
        return False

    guardar_notas(ruta, notas_restantes)
    return True


def construir_parser():
    """Construye el parser de argumentos de la interfaz de linea de comandos."""
    parser = argparse.ArgumentParser(
        prog="notas",
        description="Guarda y consulta notas rapidas en un archivo JSON local.",
    )
    parser.add_argument(
        "--archivo",
        default=RUTA_POR_DEFECTO,
        type=pathlib.Path,
        help="ruta del archivo JSON (por defecto: %(default)s)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="muestra la salida en formato JSON",
    )

    subcomandos = parser.add_subparsers(dest="comando", required=True)

    parser_add = subcomandos.add_parser("add", help="guarda una nota")
    parser_add.add_argument("texto", help="texto de la nota")
    parser_add.add_argument(
        "-t",
        "--etiqueta",
        action="append",
        default=[],
        help="etiqueta de la nota; se puede repetir",
    )

    subcomandos.add_parser("list", help="lista todas las notas")

    parser_search = subcomandos.add_parser("search", help="busca notas")
    parser_search.add_argument("consulta", help="texto o etiqueta que buscar")

    parser_delete = subcomandos.add_parser("delete", help="borra una nota")
    parser_delete.add_argument("id", type=int, help="identificador de la nota")

    return parser


def _formatear_nota(nota):
    """Convierte una nota al formato legible usado por la CLI."""
    resultado = f"[{nota['id']}] {nota['texto']}"
    etiquetas = " ".join(f"#{etiqueta}" for etiqueta in nota.get("etiquetas", []))
    if etiquetas:
        resultado += f"  {etiquetas}"
    return f"{resultado}  ({nota['creada_en']})"


def _imprimir_json(valor):
    """Escribe un valor como JSON sin escapar caracteres Unicode."""
    print(json.dumps(valor, ensure_ascii=False))


def main(argv=None) -> int:
    """Ejecuta la interfaz de linea de comandos."""
    argumentos = construir_parser().parse_args(argv)

    try:
        if argumentos.comando == "add":
            nota = agregar_nota(
                argumentos.archivo,
                argumentos.texto,
                argumentos.etiqueta,
            )
            if argumentos.json:
                _imprimir_json(nota)
            else:
                print(f"Nota añadida: {_formatear_nota(nota)}")

        elif argumentos.comando == "list":
            notas = listar_notas(argumentos.archivo)
            if argumentos.json:
                _imprimir_json(notas)
            elif notas:
                for nota in notas:
                    print(_formatear_nota(nota))
            else:
                print("Sin notas.")

        elif argumentos.comando == "search":
            notas = buscar_notas(argumentos.archivo, argumentos.consulta)
            if argumentos.json:
                _imprimir_json(notas)
            elif notas:
                for nota in notas:
                    print(_formatear_nota(nota))
            else:
                print("Sin coincidencias.")

        elif argumentos.comando == "delete":
            if not borrar_nota(argumentos.archivo, argumentos.id):
                raise ValueError(f"No existe una nota con id {argumentos.id}.")
            if argumentos.json:
                _imprimir_json({"id": argumentos.id, "eliminada": True})
            else:
                print(f"Nota {argumentos.id} eliminada.")

    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
