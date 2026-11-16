from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

CATEGORIES = (
    "instrucciones",
    "json",
    "herramientas",
    "arquitectura",
    "calculo",
    "codigo",
    "contexto_largo",
    "abstencion",
    "extraccion",
)

# Categories whose answers are code and run in the sandbox. Everything else is
# graded on text, so a run of these is a text-quality measurement.
CODE_CATEGORIES = ("codigo",)


@dataclass(frozen=True)
class Task:
    """One auto-graded item.

    The prompt and the grader live together on purpose: an item is only valid
    if the checker is deterministic and does not call another model.
    """

    id: str
    category: str
    prompt: str
    grader: str
    max_tokens: int
    expect: tuple[str, ...] = ()
    compare: str = "text"
    pattern: str | None = None
    schema: dict | None = None
    expect_json: Any = None
    tools: tuple[dict, ...] = ()
    tool_expect: dict | None = None
    prefix: str = "- "
    count: int | None = None
    min_words: int | None = None
    max_words: int | None = None
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    expect_kv: dict | None = None
    numeric_keys: tuple[str, ...] = ()
    separator: str = "|"
    parts: tuple[str, ...] = ()
    sections: tuple[str, ...] = ()
    tests: str | None = None
    code_timeout_s: int = 5
    # "py" runs the tests with the stdlib runner; "js" with node --permission.
    lang: str = "py"
    metadata: dict = field(default_factory=dict)


WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Devuelve el tiempo actual de una ciudad.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Ciudad a consultar."},
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Unidad de temperatura.",
                },
            },
            "required": ["city", "unit"],
        },
    },
}

NOTES_TOOLS = (
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "Busca una frase en las notas del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Frase a buscar."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Crea una tarea con título y fecha límite.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "due": {"type": "string", "description": "Fecha AAAA-MM-DD."},
                },
                "required": ["title", "due"],
            },
        },
    },
)

_NEEDLE_SENTENCES = (
    "El registro {n} de la sede {s} se revisó el día {d} sin incidencias.",
    "La incidencia {n} quedó cerrada en la sede {s} el día {d}.",
    "El expediente {n} pasó a archivo el día {d}, según la sede {s}.",
    "La auditoría {n} de la sede {s} se programó para el día {d}.",
    "El informe {n} de la sede {s} se envió el día {d} a la central.",
    "La revisión {n} del contrato de la sede {s} venció el día {d}.",
)


def build_needle_context(chars: int, needle: str, *, depth: float = 0.5) -> str:
    """Build deterministic filler with ``needle`` buried at a fixed depth."""

    lines: list[str] = []
    size = 0
    index = 0
    while size < chars:
        template = _NEEDLE_SENTENCES[index % len(_NEEDLE_SENTENCES)]
        line = template.format(n=1000 + index, s=1 + (index % 7), d=1 + (index % 28))
        lines.append(line)
        size += len(line) + 1
        index += 1
    position = max(1, min(len(lines) - 1, int(len(lines) * depth)))
    lines.insert(position, needle)
    return "\n".join(lines)


def build_multi_needle_context(
    chars: int,
    needles: tuple[str, ...],
    *,
    depths: tuple[float, ...] | None = None,
) -> str:
    """Build deterministic filler with several needles at fixed depths."""

    lines: list[str] = []
    size = 0
    index = 0
    while size < chars:
        template = _NEEDLE_SENTENCES[index % len(_NEEDLE_SENTENCES)]
        line = template.format(n=1000 + index, s=1 + (index % 7), d=1 + (index % 28))
        lines.append(line)
        size += len(line) + 1
        index += 1
    if depths is None:
        depths = tuple(
            0.2 + 0.55 * position / max(1, len(needles) - 1) for position in range(len(needles))
        )
    positions = sorted(
        (max(1, min(len(lines) - 1, int(len(lines) * depth))), needle)
        for depth, needle in zip(depths, needles, strict=True)
    )
    for position, needle in reversed(positions):
        lines.insert(position, needle)
    return "\n".join(lines)


def _needle_task(
    task_id: str,
    settings,
    *,
    chars: int,
    code: str,
    depth: float,
) -> Task:
    needle = f"El código de reserva es {code}."
    context = build_needle_context(chars, needle, depth=depth)
    prompt = (
        "Lee el siguiente documento y responde a la pregunta.\n\n"
        f"{context}\n\n"
        "Pregunta: ¿cuál es el código de reserva que aparece en el documento? "
        "Responde únicamente con el código, sin explicación."
    )
    return Task(
        id=task_id,
        category="contexto_largo",
        prompt=prompt,
        grader="exact",
        compare="alnum",
        expect=(code,),
        max_tokens=32,
        metadata={"context_chars": len(prompt), "needle_depth": depth},
    )


def _multi_needle_task(task_id: str, settings) -> Task:
    first = "ONICE-3141"
    second = "MAGMA-2718"
    context = build_multi_needle_context(
        settings.needle_chars,
        (
            f"El código de reserva es {first}.",
            f"El código de reserva es {second}.",
        ),
        depths=(0.28, 0.73),
    )
    prompt = (
        "Lee el siguiente documento y responde a la pregunta.\n\n"
        f"{context}\n\n"
        "Pregunta: aparecen dos códigos de reserva. Responde solo con los dos "
        "códigos separados por una coma y un espacio, en el orden en que aparecen "
        "en el documento. No expliques nada."
    )
    return Task(
        id=task_id,
        category="contexto_largo",
        prompt=prompt,
        grader="regex",
        pattern=rf"^\s*{first}\s*,\s*{second}\s*$",
        expect=(first, second),
        max_tokens=48,
        metadata={"context_chars": len(prompt), "needle_depths": (0.28, 0.73)},
    )


def build_tasks(settings) -> tuple[Task, ...]:
    """Return the eval items in a fixed order.

    Order is part of the contract: changing prompts, limits, order or graders
    requires bumping ``[eval].revision`` in ``config/eval.toml``.

    Revision 4 replaces the items every model passed. The new ones are built
    around the work the user actually does — code review and refactors, API
    contracts, architecture decisions — because arithmetic drills did not
    separate two 27B checkpoints from each other or from themselves.
    """

    tasks: list[Task] = [
        Task(
            id="es-formato-vinetas",
            category="instrucciones",
            prompt=(
                "Explica en español, en exactamente 3 viñetas, tres riesgos de guardar "
                "contraseñas en texto plano. Cada línea debe empezar por '- '. No añadas "
                "introducción, cierre ni líneas en blanco."
            ),
            grader="bullets",
            count=3,
            prefix="- ",
            min_words=5,
            max_tokens=160,
        ),
        Task(
            id="es-restricciones-triples",
            category="instrucciones",
            prompt=(
                "Resume en 25 palabras o menos qué aporta un índice B-tree en una base "
                "de datos. La respuesta debe empezar por 'Un índice'. No uses las "
                "palabras 'árbol' ni 'tree'. Responde solo con la frase."
            ),
            grader="constraints",
            max_words=25,
            min_words=8,
            include=("un índice",),
            exclude=("árbol", "arbol", "tree"),
            max_tokens=200,
        ),
        Task(
            id="json-pedido",
            category="json",
            prompt=(
                "Devuelve solo un objeto JSON, sin texto alrededor, con estos campos "
                "exactos: customer (texto), urgent (booleano), total (número) y "
                "items (entero). Datos: el cliente es 'Talleres Ríos', el pedido es "
                "urgente y son 3 artículos por 149,90 euros."
            ),
            grader="json",
            schema={
                "type": "object",
                "required": ["customer", "urgent", "total", "items"],
                "properties": {
                    "customer": {"type": "string"},
                    "urgent": {"type": "boolean"},
                    "total": {"type": "number"},
                    "items": {"type": "integer"},
                },
                "additionalProperties": False,
            },
            expect_json={"customer": "Talleres Ríos", "urgent": True, "total": 149.9, "items": 3},
            max_tokens=200,
        ),
        Task(
            id="json-api-anidado",
            category="json",
            prompt=(
                "Extrae este pedido a un objeto JSON con esta forma exacta y sin campos "
                "de más:\n"
                '- "pedido": texto\n'
                '- "prioridad": uno de "alta", "media" o "baja"\n'
                '- "lineas": lista con al menos 2 objetos, cada uno con "sku" (texto) y '
                '"qty" (entero); si una línea lleva la nota frágil, añade "nota" con el '
                'texto exacto "frágil"\n'
                '- "aviso": solo si alguna línea es frágil, con el texto exacto '
                '"manipular con cuidado"\n\n'
                "Texto: «Pedido P-1042, prioridad alta. Tres teclados TEC-01 y un "
                "soporte SOP-07 marcado como frágil.»\n"
                "Responde solo con el JSON."
            ),
            grader="json",
            schema={
                "type": "object",
                "required": ["pedido", "prioridad", "lineas", "aviso"],
                "properties": {
                    "pedido": {"type": "string"},
                    "prioridad": {"type": "string", "enum": ["alta", "media", "baja"]},
                    "lineas": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                            "type": "object",
                            "required": ["sku", "qty"],
                            "properties": {
                                "sku": {"type": "string"},
                                "qty": {"type": "integer"},
                                "nota": {"type": "string"},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "aviso": {"type": "string"},
                },
                "additionalProperties": False,
            },
            expect_json={
                "pedido": "P-1042",
                "prioridad": "alta",
                "lineas": [
                    {"sku": "TEC-01", "qty": 3},
                    {"sku": "SOP-07", "qty": 1, "nota": "frágil"},
                ],
                "aviso": "manipular con cuidado",
            },
            max_tokens=400,
        ),
        Task(
            id="json-presupuesto",
            category="json",
            prompt=(
                "Devuelve solo un objeto JSON, sin texto alrededor, con esta forma "
                "exacta: cliente (texto), lineas (lista de al menos 2 objetos con sku, "
                "qty, precio_unitario y subtotal), descuento_porcentaje (número), "
                "base_con_descuento (número), iva (número) y total (número).\n"
                "Datos: cliente 'Nortec'; 2 monitores MON-27 a 180 € cada uno; 1 dock "
                "DOCK-9 a 95 €; descuento del 20 % sobre el subtotal; IVA del 21 % "
                "sobre la base con descuento. Importes numéricos."
            ),
            grader="json",
            schema={
                "type": "object",
                "required": [
                    "cliente",
                    "lineas",
                    "descuento_porcentaje",
                    "base_con_descuento",
                    "iva",
                    "total",
                ],
                "properties": {
                    "cliente": {"type": "string"},
                    "lineas": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                            "type": "object",
                            "required": ["sku", "qty", "precio_unitario", "subtotal"],
                            "properties": {
                                "sku": {"type": "string"},
                                "qty": {"type": "integer"},
                                "precio_unitario": {"type": "number"},
                                "subtotal": {"type": "number"},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "descuento_porcentaje": {"type": "number"},
                    "base_con_descuento": {"type": "number"},
                    "iva": {"type": "number"},
                    "total": {"type": "number"},
                },
                "additionalProperties": False,
            },
            expect_json={
                "cliente": "Nortec",
                "lineas": [
                    {
                        "sku": "MON-27",
                        "qty": 2,
                        "precio_unitario": 180.0,
                        "subtotal": 360.0,
                    },
                    {
                        "sku": "DOCK-9",
                        "qty": 1,
                        "precio_unitario": 95.0,
                        "subtotal": 95.0,
                    },
                ],
                "descuento_porcentaje": 20,
                "base_con_descuento": 364.0,
                "iva": 76.44,
                "total": 440.44,
            },
            max_tokens=500,
        ),
        Task(
            id="tool-tiempo",
            category="herramientas",
            prompt=(
                "¿Qué tiempo hace ahora en Valencia? Usa la herramienta disponible y "
                "pide la temperatura en grados celsius."
            ),
            grader="tool",
            tools=(WEATHER_TOOL,),
            tool_expect={
                "name": "get_weather",
                "arguments": {"city": "Valencia", "unit": "celsius"},
            },
            max_tokens=160,
        ),
        Task(
            id="tool-orden",
            category="herramientas",
            prompt=(
                "Antes de crear la tarea 'revisar contrato', busca en las notas si ya "
                "hablamos de ese contrato. Después crea la tarea con fecha límite "
                "2026-12-01. Usa las herramientas en ese orden."
            ),
            grader="tool",
            tools=NOTES_TOOLS,
            tool_expect={
                "name": "search_notes",
                "arguments": {},
                "then": "create_task",
            },
            max_tokens=220,
        ),
        Task(
            id="tool-agenda",
            category="herramientas",
            prompt=(
                "Busca en las notas la palabra 'ACME'. Si aparece, crea la tarea "
                "'renovar contrato ACME' con fecha límite 2026-12-15. Usa "
                "search_notes primero y create_task después. No respondas con texto."
            ),
            grader="tool",
            tools=NOTES_TOOLS,
            tool_expect={
                "name": "search_notes",
                "arguments": {"query": "ACME"},
                "then": "create_task",
                "then_arguments": {"title": "renovar contrato ACME", "due": "2026-12-15"},
            },
            max_tokens=240,
        ),
        Task(
            id="arch-tradeoff",
            category="arquitectura",
            prompt=(
                "Tienes un portátil con 32 GB de memoria compartida, sin acceso a "
                "internet y con la regla de que solo puede haber un motor de modelos "
                "cargado a la vez. Dos diseños:\n"
                "A) Un único modelo de 27B siempre cargado: 16 GB de pesos, buena "
                "calidad, sin recargas.\n"
                "B) Dos modelos de 8B que se cargan y descargan según la tarea: 10 "
                "segundos de recarga cada cambio, más variedad.\n"
                "Elige uno. Responde en 60 palabras o menos, en español, diciendo qué "
                "opción descartas y por qué, y menciona el límite de 32 GB. No uses la "
                "palabra 'depende'."
            ),
            grader="constraints",
            max_words=60,
            min_words=15,
            include=("32 gb", "descart"),
            exclude=("depende",),
            max_tokens=400,
        ),
        Task(
            id="arch-contradiccion",
            category="arquitectura",
            prompt=(
                "Estas frases describen el mismo servicio. Exactamente dos se "
                "contradicen entre sí:\n"
                "1. El servicio escucha solo en 127.0.0.1:18090.\n"
                "2. Los ficheros viven en el volumen Docker curso-data.\n"
                "3. El contenedor monta curso-data en /usr/share/nginx/html en solo "
                "lectura.\n"
                "4. El puerto 2222 es Forgejo, no SSH.\n"
                "5. Al arrancar, el servicio regenera el índice y lo escribe en "
                "/usr/share/nginx/html/index.html.\n"
                "6. nginx:alpine sirve el contenido.\n"
                "Responde solo con los dos números que se contradicen, el menor "
                "primero y separados por un guion (por ejemplo 2-4)."
            ),
            grader="exact",
            compare="alnum",
            expect=("3-5",),
            max_tokens=40,
        ),
        Task(
            id="arch-adr",
            category="arquitectura",
            prompt=(
                "Escribe un ADR de exactamente 4 líneas sobre usar SQLite en lugar de "
                "ficheros JSON para el catálogo. Cada línea debe empezar por una de "
                "estas etiquetas, en este orden: 'Contexto:', 'Decisión:', "
                "'Alternativa descartada:' y 'Consecuencia:'. Máximo 60 palabras en "
                "total. No añadas nada más."
            ),
            grader="sections",
            sections=("Contexto:", "Decisión:", "Alternativa descartada:", "Consecuencia:"),
            max_words=60,
            max_tokens=400,
        ),
        Task(
            id="math-iva",
            category="calculo",
            prompt=(
                "Un portátil cuesta 1240 euros sin IVA. Con un IVA del 21 %, ¿cuál es el "
                "precio final? Responde solo con el importe en euros, con dos decimales y "
                "el símbolo €."
            ),
            grader="regex",
            pattern=r"^\s*1[.,]?500[.,]40\s*€\s*$",
            max_tokens=40,
        ),
        Task(
            id="math-fecha",
            category="calculo",
            prompt=(
                "Si hoy es 2026-10-28, ¿qué fecha será dentro de 45 días? Responde solo con "
                "la fecha en formato AAAA-MM-DD."
            ),
            grader="regex",
            pattern=r"^\s*2026-12-12\s*$",
            max_tokens=40,
        ),
        Task(
            id="math-descuento",
            category="calculo",
            prompt=(
                "Un pedido lleva 3 unidades a 49,90 € cada una. Aplica un descuento "
                "del 15 % sobre el subtotal y después un IVA del 21 % sobre el importe "
                "con descuento. Suma 4,95 € de gastos de envío. Redondea solo el "
                "resultado final a dos decimales. Responde solo con el importe y el "
                "símbolo €."
            ),
            grader="regex",
            pattern=r"^\s*158[.,]92\s*€\s*$",
            max_tokens=40,
        ),
        Task(
            id="code-js-normaliza",
            category="codigo",
            prompt=(
                "Escribe un módulo ES de JavaScript sin dependencias que exporte dos "
                "funciones:\n"
                "- `normalize(text)`: pasa a minúsculas, quita los diacríticos y deja "
                "un solo espacio entre palabras, sin espacios al principio ni al final.\n"
                "- `matches(dish, query)`: devuelve true si `dish.name` normalizado "
                "contiene `query` normalizado, y true también cuando `query` está vacío.\n"
                "Devuelve solo el código, sin explicación."
            ),
            grader="code",
            lang="js",
            tests=(
                "const eq = (got, want, what) => {\n"
                "  if (JSON.stringify(got) !== JSON.stringify(want)) {\n"
                "    throw new Error(`${what}: expected ${JSON.stringify(want)}, got ${JSON.stringify(got)}`);\n"
                "  }\n"
                "};\n"
                'eq(solution.normalize("Arròs Negre"), "arros negre", "acentos");\n'
                'eq(solution.normalize("  Sopa   de  peix "), "sopa de peix", "espacios");\n'
                'eq(solution.matches({ name: "Arròs Negre" }, "arros"), true, "consulta sin acentos");\n'
                'eq(solution.matches({ name: "Sopa" }, "ARRÒS"), false, "no debe coincidir");\n'
                'eq(solution.matches({ name: "Truita" }, ""), true, "consulta vacía");\n'
                'eq(solution.matches({ name: "  Truita  " }, "truit"), true, "coincidencia parcial");\n'
            ),
            max_tokens=900,
        ),
        Task(
            id="code-py-permisos",
            category="codigo",
            prompt=(
                "Implementa `effective(path, declared)` en Python. `path` es la ruta de "
                "una nota y `declared` es el permiso del frontmatter o None si no lo "
                "declara. Cada carpeta tiene un permiso por defecto:\n"
                "'40 Archivo/' y 'Sistema/' -> 'nadie'; '10 Proyectos/', '20 Áreas/', "
                "'30 Recursos/' y 'Plantillas/' -> 'humano'; '_Agentes/' -> 'agente'; "
                "'00 Inbox/' -> 'ambos'.\n"
                "Regla: el permiso declarado solo puede endurecer, nunca relajar. Orden "
                "de dureza, de más a menos: 'nadie', 'humano', 'agente', 'ambos'. La "
                "función devuelve el permiso efectivo como texto. Devuelve solo el "
                "código, sin explicación."
            ),
            grader="code",
            tests=(
                'assert solution.effective("40 Archivo/nota.md", "ambos") == "nadie"\n'
                'assert solution.effective("40 Archivo/nota.md", "humano") == "nadie"\n'
                'assert solution.effective("_Agentes/nota.md", "humano") == "humano"\n'
                'assert solution.effective("_Agentes/nota.md", "ambos") == "agente"\n'
                'assert solution.effective("10 Proyectos/x.md", None) == "humano"\n'
                'assert solution.effective("10 Proyectos/x.md", "agente") == "humano"\n'
                'assert solution.effective("00 Inbox/x.md", None) == "ambos"\n'
                'assert solution.effective("00 Inbox/x.md", "agente") == "agente"\n'
                'assert solution.effective("Sistema/x.md", "ambos") == "nadie"\n'
            ),
            max_tokens=700,
        ),
        Task(
            id="code-py-sqlite",
            category="codigo",
            prompt=(
                "Implementa `top_clientes(conn, minimo)` en Python. `conn` es una "
                "conexión sqlite3 con las tablas clientes(id, nombre) y "
                "pedidos(id, cliente_id, total). Devuelve una lista de tuplas "
                "(nombre, total) con los clientes que tienen al menos `minimo` pedidos, "
                "ordenada por total descendente y, en empate, por nombre ascendente. "
                "Devuelve solo el código, sin explicación."
            ),
            grader="code",
            tests=(
                "import sqlite3\n"
                'conn = sqlite3.connect(":memory:")\n'
                'conn.executescript("create table clientes(id integer primary key, nombre text);"\n'
                '                   "create table pedidos(id integer primary key, cliente_id integer, total real);")\n'
                'conn.executemany("insert into clientes values (?, ?)",\n'
                '                 [(1, "Ana"), (2, "Luis"), (3, "Marta"), (4, "Pablo")])\n'
                'conn.executemany("insert into pedidos values (?, ?, ?)",\n'
                "                 [(1, 1, 100.0), (2, 1, 50.0), (3, 2, 30.0),\n"
                "                  (4, 3, 70.0), (5, 3, 20.0), (6, 4, 500.0)])\n"
                'assert solution.top_clientes(conn, 2) == [("Ana", 150.0), ("Marta", 90.0)]\n'
                'assert solution.top_clientes(conn, 1) == [("Pablo", 500.0), ("Ana", 150.0), ("Marta", 90.0), ("Luis", 30.0)]\n'
                "assert solution.top_clientes(conn, 3) == []\n"
            ),
            max_tokens=700,
        ),
        Task(
            id="code-py-ranges",
            category="codigo",
            prompt=(
                "Implementa `merge_ranges(ranges)` en Python. Cada rango es una tupla "
                "(inicio, fin) inclusive. Fusiona los rangos que se solapen o sean "
                "adyacentes (por ejemplo (1, 2) y (3, 4) -> (1, 4)), ordena el "
                "resultado y devuelve una lista de tuplas. No modifiques la entrada. "
                "Devuelve solo el código, sin explicación."
            ),
            grader="code",
            tests=(
                "assert solution.merge_ranges([(1, 3), (2, 6), (8, 10), (15, 18)]) == [(1, 6), (8, 10), (15, 18)]\n"
                "assert solution.merge_ranges([(5, 7), (1, 2), (3, 4)]) == [(1, 7)]\n"
                "assert solution.merge_ranges([]) == []\n"
                "assert solution.merge_ranges([(4, 5), (1, 2)]) == [(1, 2), (4, 5)]\n"
                "assert solution.merge_ranges([(1, 10), (2, 3), (4, 5)]) == [(1, 10)]\n"
                "assert solution.merge_ranges([(-5, -1), (-2, 0), (2, 2)]) == [(-5, 0), (2, 2)]\n"
                "ranges = [(1, 2), (3, 4)]\n"
                "solution.merge_ranges(ranges)\n"
                "assert ranges == [(1, 2), (3, 4)]\n"
            ),
            max_tokens=900,
        ),
        Task(
            id="code-py-lru",
            category="codigo",
            prompt=(
                "Implementa `LRUCache` en Python con `__init__(capacity)`, `get(key)` "
                "y `put(key, value)` en O(1). `get` devuelve el valor o -1. `put` "
                "actualiza si la clave existe, inserta si no, y expulsa la clave menos "
                "usada recientemente cuando se supera `capacity`. Con capacity 0 no se "
                "almacena nada. Devuelve solo el código, sin explicación."
            ),
            grader="code",
            tests=(
                "c = solution.LRUCache(2)\n"
                "c.put(1, 1)\n"
                "c.put(2, 2)\n"
                "assert c.get(1) == 1\n"
                "c.put(3, 3)\n"
                "assert c.get(2) == -1\n"
                "assert c.get(3) == 3\n"
                "assert c.get(1) == 1\n"
                "c = solution.LRUCache(2)\n"
                "c.put(1, 1)\n"
                "c.put(1, 10)\n"
                "assert c.get(1) == 10\n"
                "c.put(2, 2)\n"
                "c.put(3, 3)\n"
                "assert c.get(1) == -1\n"
                "assert c.get(2) == 2\n"
                "c = solution.LRUCache(0)\n"
                "c.put(1, 1)\n"
                "assert c.get(1) == -1\n"
                "c = solution.LRUCache(1)\n"
                "c.put(1, 1)\n"
                "c.put(2, 2)\n"
                "assert c.get(1) == -1\n"
                "assert c.get(2) == 2\n"
            ),
            max_tokens=1200,
        ),
        _needle_task(
            "needle-24k",
            settings,
            chars=settings.needle_chars,
            code="ZAFIRO-4821",
            depth=0.5,
        ),
        _needle_task(
            "needle-64k-tokens",
            settings,
            chars=settings.needle_long_chars,
            code="CUARZO-7390",
            depth=0.62,
        ),
        _multi_needle_task("needle-dos", settings),
        Task(
            id="abstain-telefono",
            category="abstencion",
            prompt=(
                "Contacto: Marta Ruiz, responsable de compras, correo marta@ejemplo.es. "
                "¿Cuál es su número de teléfono? Si el dato no aparece, responde "
                "exactamente 'NO CONSTA'."
            ),
            grader="regex",
            pattern=r"^\s*no consta\.?\s*$",
            max_tokens=24,
        ),
        Task(
            id="abstain-version",
            category="abstencion",
            prompt=(
                "Notas de publicación: «Publicado el 3 de noviembre. Se corrige el "
                "filtro de acentos, se añade exportación a CSV y baja el tiempo de "
                "arranque un 20 %.» ¿Qué número de versión se publicó? Si el dato no "
                "aparece, responde exactamente 'NO CONSTA'."
            ),
            grader="regex",
            pattern=r"^\s*no consta\.?\s*$",
            max_tokens=24,
        ),
        Task(
            id="extract-factura",
            category="extraccion",
            prompt=(
                "Factura de Servicios Roca SL, NIF B-12345678. Base imponible 1.250,00 "
                "euros, IVA 21 % (262,50 euros), total 1.512,50 euros. Extrae el NIF, la "
                "base y el IVA en tres líneas con el formato 'clave: valor' y nada más."
            ),
            grader="kv",
            expect_kv={"nif": "B-12345678", "base": "1250.00", "iva": "262.50"},
            numeric_keys=("base", "iva"),
            max_tokens=160,
        ),
        Task(
            id="extract-traza",
            category="extraccion",
            prompt=(
                "Traza de error:\n"
                "Traceback (most recent call last):\n"
                '  File "app/facturas.py", line 42, in calcular_total\n'
                "    return sum(linea.importe for linea in factura.lineas)\n"
                "TypeError: unsupported operand type(s) for +: 'NoneType' and 'float'\n"
                "POST /api/facturas/9 -> 500\n"
                "Responde en una sola línea con tres campos separados por '|': el tipo "
                "de excepción, la función donde falla y el código HTTP. Sin espacios "
                "alrededor de las barras."
            ),
            grader="parts",
            separator="|",
            parts=("TypeError", "calcular_total", "500"),
            max_tokens=160,
        ),
    ]

    headroom = getattr(settings, "reasoning_headroom", 0)
    if headroom:
        tasks = [replace(task, max_tokens=task.max_tokens + headroom) for task in tasks]
    return tuple(tasks)
