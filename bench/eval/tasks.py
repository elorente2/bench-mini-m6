from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

CATEGORIES = (
    "instrucciones",
    "json",
    "herramientas",
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
    tests: str | None = None
    code_timeout_s: int = 5
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


def build_tasks(settings) -> tuple[Task, ...]:
    """Return the eval items in a fixed order.

    Order is part of the contract: changing prompts, limits, order or graders
    requires bumping ``[eval].revision`` in ``config/eval.toml``.
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
            id="es-limite-palabras",
            category="instrucciones",
            prompt=(
                "Resume qué es una VPN en una sola frase de 20 palabras como máximo. "
                "No uses la palabra 'túnel' ni sus derivados. Responde solo con la frase."
            ),
            grader="constraints",
            max_words=20,
            min_words=8,
            exclude=("túnel", "tunel"),
            max_tokens=80,
        ),
        Task(
            id="es-fecha-larga",
            category="instrucciones",
            prompt=(
                "Convierte la fecha 2026-03-08 a español, con el formato "
                "'día de mes de año' y sin ceros a la izquierda. Responde solo con la "
                "fecha, sin punto final."
            ),
            grader="regex",
            pattern=r"^\s*8 de marzo de 2026\.?\s*$",
            max_tokens=40,
        ),
        Task(
            id="json-pedido",
            category="json",
            prompt=(
                "Extrae los datos de este pedido y responde solo con un objeto JSON, sin "
                "explicación y con exactamente estas claves: order_id (entero), "
                "customer (texto), total_eur (número), status (texto).\n\n"
                "Pedido 4471 del 12/03/2026. Cliente: Marta Ruiz. "
                "Total: 89,50 EUR. Estado: enviado."
            ),
            grader="json",
            schema={
                "type": "object",
                "required": ["order_id", "customer", "total_eur", "status"],
                "properties": {
                    "order_id": {"type": "integer"},
                    "customer": {"type": "string"},
                    "total_eur": {"type": "number"},
                    "status": {"type": "string"},
                },
                "additionalProperties": False,
            },
            expect_json={
                "order_id": 4471,
                "customer": "Marta Ruiz",
                "total_eur": 89.5,
                "status": "enviado",
            },
            max_tokens=160,
        ),
        Task(
            id="json-clasificacion",
            category="json",
            prompt=(
                "Clasifica este mensaje de soporte. Responde solo con JSON con las claves "
                "category (una de: facturacion, tecnico, otro), urgent (booleano) y summary "
                "(texto de 12 palabras como máximo). Marca urgent=true solo si el mensaje "
                "pide una acción con fecha límite.\n\n"
                "Mensaje: 'Me habéis cobrado dos veces la cuota de octubre. Necesito la "
                "devolución antes del viernes.'"
            ),
            grader="json",
            schema={
                "type": "object",
                "required": ["category", "urgent", "summary"],
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["facturacion", "tecnico", "otro"],
                    },
                    "urgent": {"type": "boolean"},
                    "summary": {"type": "string"},
                },
            },
            expect_json={"category": "facturacion", "urgent": True},
            max_tokens=160,
        ),
        Task(
            id="json-articulos",
            category="json",
            prompt=(
                "Del texto, extrae los artículos. Responde solo con JSON con la forma "
                '{"items": [{"sku": texto, "qty": entero}]} en el orden en que aparecen '
                "y sin claves extra.\n\n"
                "Pedido: 2 unidades de SKU-11 y 1 unidad de SKU-42; además 5 unidades "
                "de SKU-07."
            ),
            grader="json",
            schema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "minItems": 3,
                        "maxItems": 3,
                        "items": {
                            "type": "object",
                            "required": ["sku", "qty"],
                            "properties": {
                                "sku": {"type": "string"},
                                "qty": {"type": "integer"},
                            },
                            "additionalProperties": False,
                        },
                    }
                },
            },
            expect_json={
                "items": [
                    {"sku": "SKU-11", "qty": 2},
                    {"sku": "SKU-42", "qty": 1},
                    {"sku": "SKU-07", "qty": 5},
                ]
            },
            max_tokens=220,
        ),
        Task(
            id="tool-tiempo",
            category="herramientas",
            prompt=(
                "¿Qué tiempo hace ahora en Valencia? Usa la herramienta disponible y pide "
                "la temperatura en grados centígrados. No respondas con texto."
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
                "Primero busca en mis notas la frase 'presupuesto 2027'. Después crea una "
                "tarea para revisarla el 2026-11-20. Usa las herramientas; no respondas con texto."
            ),
            grader="tool",
            tools=NOTES_TOOLS,
            tool_expect={"name": "search_notes", "arguments": {"query": "presupuesto 2027"}},
            max_tokens=160,
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
            id="math-tornillos",
            category="calculo",
            prompt=(
                "Una caja trae 12 filas de 8 tornillos. Se han usado 37 tornillos. "
                "¿Cuántos quedan? Responde solo con el número."
            ),
            grader="regex",
            pattern=r"^\s*59\s*\.?\s*$",
            max_tokens=24,
        ),
        Task(
            id="code-merge-intervals",
            category="codigo",
            prompt=(
                "Escribe una función merge_intervals(intervals) que reciba una lista de "
                "intervalos cerrados [inicio, fin], fusione los que se solapan o se tocan y "
                "devuelva la lista ordenada. Devuelve solo el código de la función, sin "
                "explicación."
            ),
            grader="code",
            max_tokens=700,
            code_timeout_s=settings.code_timeout_s,
            tests=(
                "assert solution.merge_intervals([[1,3],[2,6],[8,10],[15,18]]) "
                "== [[1,6],[8,10],[15,18]]\n"
                "assert solution.merge_intervals([[1,4],[4,5]]) == [[1,5]]\n"
                "assert solution.merge_intervals([]) == []\n"
                "assert solution.merge_intervals([[5,6],[1,2]]) == [[1,2],[5,6]]\n"
                "assert solution.merge_intervals([[1,10],[2,3]]) == [[1,10]]\n"
            ),
        ),
        Task(
            id="code-wordcount",
            category="codigo",
            prompt=(
                "Escribe una función count_words(text) que devuelva un diccionario con la "
                "frecuencia de cada palabra en minúsculas, ignorando la puntuación y los "
                "espacios múltiples. Devuelve solo el código de la función."
            ),
            grader="code",
            max_tokens=500,
            code_timeout_s=settings.code_timeout_s,
            tests=(
                "r = solution.count_words('Hola, mundo. Hola otra vez!')\n"
                "assert r == {'hola': 2, 'mundo': 1, 'otra': 1, 'vez': 1}, r\n"
                "assert solution.count_words('') == {}\n"
                "assert solution.count_words('Uno uno UNO') == {'uno': 3}\n"
            ),
        ),
        Task(
            id="code-bugfix",
            category="codigo",
            prompt=(
                "Esta función debería devolver la longitud de la racha más larga de valores "
                "iguales consecutivos, y devolver 0 para una lista vacía, pero está mal. "
                "Corrígela y devuelve solo el código completo de la función con el mismo "
                "nombre.\n\n"
                "```python\n"
                "def longest_run(xs):\n"
                "    best = 1\n"
                "    current = 1\n"
                "    for index in range(len(xs)):\n"
                "        if xs[index] == xs[index - 1]:\n"
                "            current += 1\n"
                "        else:\n"
                "            current = 1\n"
                "        best = max(best, current)\n"
                "    return best\n"
                "```"
            ),
            grader="code",
            max_tokens=400,
            code_timeout_s=settings.code_timeout_s,
            tests=(
                "assert solution.longest_run([]) == 0\n"
                "assert solution.longest_run([7]) == 1\n"
                "assert solution.longest_run([1,1,2,2,2,1]) == 3\n"
                "assert solution.longest_run([1,2,3]) == 1\n"
                "assert solution.longest_run([4,4,4,4]) == 4\n"
            ),
        ),
        _needle_task(
            "needle-24k",
            settings,
            chars=settings.needle_chars,
            code="ZAFIRO-4821",
            depth=0.42,
        ),
        _needle_task(
            "needle-64k",
            settings,
            chars=settings.needle_long_chars,
            code="CUARZO-7390",
            depth=0.77,
        ),
        Task(
            id="abstain-telefono",
            category="abstencion",
            prompt=(
                "Texto: 'La jornada de puertas abiertas será el 14 de noviembre a las 18:00 "
                "en el salón de actos. La entrada es libre hasta completar aforo y no hace "
                "falta inscripción.'\n\n"
                "Pregunta: ¿cuál es el teléfono de contacto de la jornada? Si el dato no "
                "aparece en el texto, responde exactamente NO CONSTA."
            ),
            grader="regex",
            pattern=r"^\s*no consta\.?\s*$",
            max_tokens=24,
        ),
        Task(
            id="abstain-empleados",
            category="abstencion",
            prompt=(
                "Texto: 'La empresa abrió tres oficinas en 2024 y facturó 2,1 millones de "
                "euros. Su plantilla creció durante el año.'\n\n"
                "Pregunta: según el texto, ¿cuántos empleados tiene la empresa? Si el dato "
                "no aparece, responde exactamente NO CONSTA."
            ),
            grader="regex",
            pattern=r"^\s*no consta\.?\s*$",
            max_tokens=24,
        ),
        Task(
            id="extract-factura",
            category="extraccion",
            prompt=(
                "Factura F-2026-118. Emisor: Talleres Ribera, S.L. NIF: B-12345678. "
                "Base imponible: 1.250,00 €. IVA (21 %): 262,50 €. Total: 1.512,50 €.\n\n"
                "Extrae NIF, base imponible e IVA. Responde solo con tres líneas con el "
                "formato 'NIF: valor', 'Base: valor' e 'IVA: valor', sin el símbolo € y sin "
                "separador de miles."
            ),
            grader="kv",
            expect_kv={"nif": "B-12345678", "base": "1250.00", "iva": "262.50"},
            numeric_keys=("base", "iva"),
            max_tokens=100,
        ),
        Task(
            id="extract-agenda",
            category="extraccion",
            prompt=(
                "Reunión de equipo: jueves 13 de noviembre a las 17:30 en la sala Magnolia. "
                "Asistentes: Ana, Luis, Marta y Pablo.\n\n"
                "Responde solo con una línea en el formato 'hora | lugar | asistentes'. Usa "
                "24 horas, el nombre de la sala tal cual y separa los asistentes con comas, "
                "en el orden del texto y sin la conjunción 'y'."
            ),
            grader="parts",
            separator="|",
            parts=("17:30", "sala Magnolia", "Ana, Luis, Marta, Pablo"),
            max_tokens=100,
        ),
        Task(
            id="extract-responsable",
            category="extraccion",
            prompt=(
                "Acta de la reunión del 4 de noviembre. Asistentes: Paula, Diego y Rosa. "
                "Acuerdos: Diego revisará el contrato antes del 12 de noviembre; Paula "
                "enviará el informe final. Próxima reunión: 2 de diciembre.\n\n"
                "Pregunta: ¿quién revisará el contrato? Responde solo con el nombre."
            ),
            grader="exact",
            expect=("Diego",),
            max_tokens=24,
        ),
    ]

    headroom = getattr(settings, "reasoning_headroom", 0)
    if headroom:
        tasks = [replace(task, max_tokens=task.max_tokens + headroom) for task in tasks]
    return tuple(tasks)
