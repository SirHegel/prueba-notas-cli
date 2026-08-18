# notas-cli

`notas-cli` es una herramienta de línea de comandos escrita en Python para guardar, listar, buscar y borrar notas rápidas. Las notas se conservan localmente en un archivo JSON, incluyen un identificador incremental, etiquetas opcionales y la fecha de creación en UTC.

## Instalación

- Python 3.9 o posterior.

No hay dependencias externas para usar la herramienta. Descarga o copia esta
carpeta, entra en ella y comprueba la instalación con:

```console
$ cd notas-cli
$ python3 notas.py --help
```

`pytest` solo es necesario para ejecutar los tests; se puede instalar con
`python3 -m pip install pytest`.

## Archivo de datos

Por defecto, las notas se guardan en:

```text
~/.notas-cli/notas.json
```

El directorio y el archivo se crean automáticamente al guardar la primera nota. La ubicación se puede cambiar con la opción global `--archivo`, que debe escribirse antes del comando:

```console
$ python3 notas.py --archivo /ruta/a/mis-notas.json list
```

También se puede definir la variable de entorno `NOTAS_CLI_FILE`:

```console
$ NOTAS_CLI_FILE=/ruta/a/mis-notas.json python3 notas.py list
```

Si se usan ambos mecanismos, `--archivo` tiene prioridad sobre `NOTAS_CLI_FILE`.

## Uso

Las fechas de los ejemplos son ilustrativas: la herramienta muestra la fecha real de creación en formato ISO 8601 y UTC.

### Guardar una nota

`-t` (o `--etiqueta`) añade una etiqueta y puede repetirse para asignar varias.

```console
$ python3 notas.py add "Comprar café" -t casa
Nota añadida: [1] Comprar café  #casa  (2026-08-18T15:30:00.000000+00:00)
```

### Listar las notas

```console
$ python3 notas.py list
[1] Comprar café  #casa  (2026-08-18T15:30:00.000000+00:00)
[2] Preparar informe  #trabajo  (2026-08-18T15:35:00.000000+00:00)
```

Si no hay notas guardadas, la salida es `Sin notas.`.

### Buscar notas

La búsqueda encuentra coincidencias parciales en el texto o las etiquetas, sin distinguir mayúsculas, minúsculas ni acentos.

```console
$ python3 notas.py search "cafe"
[1] Comprar café  #casa  (2026-08-18T15:30:00.000000+00:00)
```

Si no hay resultados, la salida es `Sin coincidencias.`.

### Borrar una nota

El argumento del comando es el identificador numérico de la nota.

```console
$ python3 notas.py delete 2
Nota 2 eliminada.
```

La opción global `--json`, escrita antes del comando, devuelve resultados
aptos para otros programas:

```console
$ python3 notas.py --json list
[{"id": 1, "texto": "Comprar café", "etiquetas": ["casa"], "creada_en": "2026-08-18T15:30:00.000000+00:00"}]
```

## Formato JSON

El archivo contiene una lista JSON. Cada nota tiene los campos `id` (identificador incremental), `texto`, `etiquetas` (lista de cadenas) y `creada_en` (fecha ISO 8601 en UTC). Por ejemplo:

```json
[
  {
    "id": 1,
    "texto": "Comprar café",
    "etiquetas": [
      "casa"
    ],
    "creada_en": "2026-08-18T15:30:00.000000+00:00"
  },
  {
    "id": 2,
    "texto": "Preparar informe",
    "etiquetas": [
      "trabajo"
    ],
    "creada_en": "2026-08-18T15:35:00.000000+00:00"
  }
]
```

## Tests

Desde la carpeta del proyecto, instala `pytest` si todavía no está disponible y ejecuta:

```console
$ python3 -m pytest
```

## Códigos de salida

| Código | Significado |
| ---: | --- |
| 0 | Operación completada con éxito. |
| 1 | Error al procesar la operación. |
