import json

import pytest

import notas


def test_cargar_notas_devuelve_lista_vacia_si_archivo_no_existe(tmp_path):
    archivo = tmp_path / "notas.json"

    assert notas.cargar_notas(archivo) == []


def test_agregar_nota_persiste_y_asigna_ids_incrementales(tmp_path):
    archivo = tmp_path / "notas.json"

    creadas = [
        notas.agregar_nota(archivo, "Primera"),
        notas.agregar_nota(archivo, "Segunda", ["trabajo"]),
        notas.agregar_nota(archivo, "Tercera"),
    ]

    assert [nota["id"] for nota in creadas] == [1, 2, 3]
    assert notas.cargar_notas(archivo) == creadas
    assert json.loads(archivo.read_text(encoding="utf-8")) == creadas


@pytest.mark.parametrize("texto", ["", "   ", "\t\n"])
def test_agregar_nota_rechaza_texto_vacio_o_espacios(tmp_path, texto):
    archivo = tmp_path / "notas.json"

    with pytest.raises(ValueError, match="no puede estar vacio"):
        notas.agregar_nota(archivo, texto)

    assert not archivo.exists()


def test_listar_notas_ordena_por_id(tmp_path):
    archivo = tmp_path / "notas.json"
    desordenadas = [
        {"id": 3, "texto": "Tres", "etiquetas": [], "creada_en": "fecha-3"},
        {"id": 1, "texto": "Uno", "etiquetas": [], "creada_en": "fecha-1"},
        {"id": 2, "texto": "Dos", "etiquetas": [], "creada_en": "fecha-2"},
    ]
    notas.guardar_notas(archivo, desordenadas)

    assert [nota["id"] for nota in notas.listar_notas(archivo)] == [1, 2, 3]


def test_buscar_notas_por_fragmento_sin_importar_mayusculas(tmp_path):
    archivo = tmp_path / "notas.json"
    esperada = notas.agregar_nota(archivo, "Comprar Leche")
    notas.agregar_nota(archivo, "Llamar al banco")

    assert notas.buscar_notas(archivo, "comprar") == [esperada]
    assert notas.buscar_notas(archivo, "LECHE") == [esperada]


def test_buscar_notas_pliega_acentos_y_busca_en_etiquetas(tmp_path):
    archivo = tmp_path / "notas.json"
    por_acento = notas.agregar_nota(archivo, "Reunión del miércoles")
    por_etiqueta = notas.agregar_nota(archivo, "Preparar informe", ["Administración"])

    assert notas.buscar_notas(archivo, "reunion") == [por_acento]
    assert notas.buscar_notas(archivo, "ADMINISTRACION") == [por_etiqueta]


def test_buscar_notas_devuelve_vacio_sin_coincidencias(tmp_path):
    archivo = tmp_path / "notas.json"
    notas.agregar_nota(archivo, "Comprar pan", ["casa"])

    assert notas.buscar_notas(archivo, "vacaciones") == []


def test_borrar_nota_existente_devuelve_true_y_reduce_lista(tmp_path):
    archivo = tmp_path / "notas.json"
    notas.agregar_nota(archivo, "Uno")
    notas.agregar_nota(archivo, "Dos")

    assert notas.borrar_nota(archivo, 1) is True
    assert [nota["id"] for nota in notas.cargar_notas(archivo)] == [2]


def test_borrar_nota_inexistente_devuelve_false_y_no_cambia_lista(tmp_path):
    archivo = tmp_path / "notas.json"
    creada = notas.agregar_nota(archivo, "Conservar")

    assert notas.borrar_nota(archivo, 99) is False
    assert notas.cargar_notas(archivo) == [creada]


def test_cargar_notas_con_json_corrupto_lanza_error_esperado(tmp_path):
    archivo = tmp_path / "notas.json"
    archivo.write_text('{"id": ', encoding="utf-8")

    with pytest.raises(ValueError, match="contiene JSON corrupto"):
        notas.cargar_notas(archivo)


def test_main_add(tmp_path, capsys):
    archivo = tmp_path / "notas.json"

    codigo = notas.main(
        ["--archivo", str(archivo), "add", "Comprar café", "-t", "casa"]
    )

    salida = capsys.readouterr()
    assert codigo == 0
    assert "Nota añadida: [1] Comprar café" in salida.out
    assert "#casa" in salida.out
    assert salida.err == ""
    assert notas.cargar_notas(archivo)[0]["texto"] == "Comprar café"


def test_main_list(tmp_path, capsys):
    archivo = tmp_path / "notas.json"
    notas.agregar_nota(archivo, "Nota visible", ["demo"])

    codigo = notas.main(["--archivo", str(archivo), "list"])

    salida = capsys.readouterr()
    assert codigo == 0
    assert "[1] Nota visible" in salida.out
    assert "#demo" in salida.out
    assert salida.err == ""


def test_main_search(tmp_path, capsys):
    archivo = tmp_path / "notas.json"
    notas.agregar_nota(archivo, "Reunión de equipo")
    notas.agregar_nota(archivo, "Comprar fruta")

    codigo = notas.main(["--archivo", str(archivo), "search", "REUNION"])

    salida = capsys.readouterr()
    assert codigo == 0
    assert "Reunión de equipo" in salida.out
    assert "Comprar fruta" not in salida.out
    assert salida.err == ""


def test_main_delete(tmp_path, capsys):
    archivo = tmp_path / "notas.json"
    notas.agregar_nota(archivo, "Eliminar esta nota")

    codigo = notas.main(["--archivo", str(archivo), "delete", "1"])

    salida = capsys.readouterr()
    assert codigo == 0
    assert salida.out == "Nota 1 eliminada.\n"
    assert salida.err == ""
    assert notas.cargar_notas(archivo) == []


def test_main_delete_fallido(tmp_path, capsys):
    archivo = tmp_path / "notas.json"

    codigo = notas.main(["--archivo", str(archivo), "delete", "404"])

    salida = capsys.readouterr()
    assert codigo == 1
    assert salida.out == ""
    assert salida.err == "Error: No existe una nota con id 404.\n"

