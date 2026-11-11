"""Vision items: deterministic images with an answer we already know.

Every fixture is drawn in code, so the expected answer cannot drift from the
image and no binary file has to be committed. The result records the image hash,
which makes a wrong grade traceable to a wrong fixture.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from .png import canvas, fill_circle, fill_rect, write_png

RED = (200, 30, 30)
BLUE = (30, 60, 200)
GREEN = (30, 150, 60)
YELLOW = (240, 200, 40)
WHITE = (255, 255, 255)


@dataclass(frozen=True)
class VisionTask:
    id: str
    prompt: str
    image: bytes
    expect: tuple[str, ...]
    max_tokens: int = 24
    metadata: dict = field(default_factory=dict)

    @property
    def image_sha256(self) -> str:
        return hashlib.sha256(self.image).hexdigest()


def _triangle(rows, x0: int, y0: int, size: int, color) -> None:
    for step in range(size):
        fill_rect(rows, x0 + (size - step), y0 + step, x0 + size + step, y0 + step + 1, color)


# Seven-segment layout: which bars are lit for each digit.
_SEGMENTS = {
    "0": "abcdef",
    "1": "bc",
    "2": "abged",
    "3": "abgcd",
    "4": "fgbc",
    "5": "afgcd",
    "6": "afgedc",
    "7": "abc",
    "8": "abcdefg",
    "9": "abcfgd",
}


def draw_digit(
    rows, x0: int, y0: int, width: int, height: int, thickness: int, digit: str, color
) -> None:
    """Draw one digit as seven rectangular bars, like a calculator display."""

    half = height // 2
    bars = {
        "a": (x0, y0, x0 + width, y0 + thickness),
        "b": (x0 + width - thickness, y0, x0 + width, y0 + half),
        "c": (x0 + width - thickness, y0 + half, x0 + width, y0 + height),
        "d": (x0, y0 + height - thickness, x0 + width, y0 + height),
        "e": (x0, y0 + half, x0 + thickness, y0 + height),
        "f": (x0, y0, x0 + thickness, y0 + half),
        "g": (x0, y0 + half - thickness // 2, x0 + width, y0 + half + thickness // 2),
    }
    for bar in _SEGMENTS[digit]:
        fill_rect(rows, *bars[bar], color)


def build_tasks(settings) -> tuple[VisionTask, ...]:
    size = settings.image_size
    tasks: list[VisionTask] = []

    # 1. Count one colour: three red circles among blue squares.
    rows = canvas(size, size)
    for cx, cy in ((60, 60), (160, 60), (260, 60)):
        fill_circle(rows, cx, cy, 28, RED)
    fill_rect(rows, 40, 150, 100, 210, BLUE)
    fill_rect(rows, 160, 150, 220, 210, BLUE)
    tasks.append(
        VisionTask(
            id="vision-conteo",
            prompt=(
                "En la imagen hay círculos rojos y cuadrados azules. "
                "¿Cuántos círculos rojos hay? Responde solo con el número."
            ),
            image=write_png(rows),
            expect=("3",),
            metadata={"fixture": "3 red circles, 2 blue squares"},
        )
    )

    # 2. Majority colour by area.
    rows = canvas(size, size)
    fill_rect(rows, 0, 0, size, 210, GREEN)
    fill_rect(rows, 0, 210, size, size, YELLOW)
    tasks.append(
        VisionTask(
            id="vision-color",
            prompt=(
                "La imagen está dividida en dos franjas horizontales, una verde y "
                "otra amarilla. ¿Qué color ocupa más superficie? Responde solo con "
                "el color."
            ),
            image=write_png(rows),
            expect=("verde",),
            metadata={"fixture": "green 210/320, yellow 110/320"},
        )
    )

    # 3. Relative position.
    rows = canvas(size, size)
    fill_rect(rows, 40, 110, 140, 210, RED)
    fill_circle(rows, 240, 160, 50, BLUE)
    tasks.append(
        VisionTask(
            id="vision-posicion",
            prompt=(
                "Hay un cuadrado rojo y un círculo azul. ¿El círculo azul está a la "
                "izquierda o a la derecha del cuadrado rojo? Responde solo con "
                "'izquierda' o 'derecha'."
            ),
            image=write_png(rows),
            expect=("derecha",),
            metadata={"fixture": "red square left, blue circle right"},
        )
    )

    # 4. Total count across shapes and colours.
    rows = canvas(size, size)
    fill_circle(rows, 80, 80, 34, RED)
    fill_rect(rows, 200, 50, 280, 130, BLUE)
    _triangle(rows, 40, 190, 80, GREEN)
    fill_circle(rows, 220, 230, 34, YELLOW)
    tasks.append(
        VisionTask(
            id="vision-total",
            prompt=(
                "Cuenta todas las figuras de la imagen, sin importar forma ni color. "
                "Responde solo con el número."
            ),
            image=write_png(rows),
            expect=("4",),
            metadata={"fixture": "circle, square, triangle, circle"},
        )
    )

    # 5. Read a seven-segment digit: this one needs real recognition, not a
    # colour prior.
    rows = canvas(size, size)
    draw_digit(rows, 110, 40, 100, 240, 18, "6", RED)
    tasks.append(
        VisionTask(
            id="vision-digito",
            prompt=(
                "La imagen muestra un número dibujado con barras, como en una "
                "calculadora. ¿Qué número es? Responde solo con el dígito."
            ),
            image=write_png(rows),
            expect=("6",),
            metadata={"fixture": "seven-segment 6"},
        )
    )

    # 6. Occlusion: the centre of the image belongs to the circle painted last.
    rows = canvas(size, size)
    fill_circle(rows, 140, 160, 70, BLUE)
    fill_circle(rows, 180, 160, 70, RED)
    tasks.append(
        VisionTask(
            id="vision-solape",
            prompt=(
                "Hay dos círculos que se solapan: uno azul y otro rojo. En el "
                "centro exacto de la imagen solo se ve un color. ¿Cuál es? "
                "Responde solo con el color."
            ),
            image=write_png(rows),
            expect=("rojo",),
            metadata={"fixture": "blue circle overdrawn by red at the centre"},
        )
    )

    # 7. Counting at scale: nine small circles, no colour distractor.
    rows = canvas(size, size)
    spots = (
        (45, 45),
        (150, 35),
        (260, 55),
        (80, 130),
        (190, 120),
        (285, 150),
        (50, 230),
        (160, 255),
        (265, 240),
    )
    for cx, cy in spots:
        fill_circle(rows, cx, cy, 16, RED)
    tasks.append(
        VisionTask(
            id="vision-cuentanueve",
            prompt="¿Cuántos círculos rojos hay en la imagen? Responde solo con el número.",
            image=write_png(rows),
            expect=("9",),
            metadata={"fixture": "9 scattered red circles"},
        )
    )

    # 8. Read a three-digit seven-segment number.
    rows = canvas(size, size)
    for offset, digit in zip((34, 126, 218), "417", strict=True):
        draw_digit(rows, offset, 70, 68, 180, 14, digit, RED)
    tasks.append(
        VisionTask(
            id="vision-digitos",
            prompt=(
                "La imagen muestra un número de tres cifras dibujado con barras, "
                "como en una calculadora. ¿Qué número es? Responde solo con las "
                "tres cifras, sin espacios."
            ),
            image=write_png(rows),
            expect=("417",),
            metadata={"fixture": "seven-segment 417"},
        )
    )

    return tuple(tasks)
