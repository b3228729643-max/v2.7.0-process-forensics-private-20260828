from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")


def f(value) -> float:
    return float(value)


def point(cm, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, g = map(float, cm)
    return a * x + c * y + e, b * x + d * y + g


@dataclass
class Style:
    stroke: tuple[float, ...] = (0.0,)
    fill: tuple[float, ...] = (0.0,)
    width: float = 1.0
    dash: tuple[tuple[float, ...], float] = ((), 0.0)


@dataclass
class PaintedPath:
    sequence: int
    paint_op: str
    bbox: tuple[float, float, float, float]
    point_count: int
    style: Style
    points: tuple[tuple[float, float], ...]


paths: list[PaintedPath] = []
current: list[tuple[float, float]] = []
style = Style()
stack: list[Style] = []
sequence = 0


def visitor(op, args, cm, tm):
    global current, style, sequence
    name = op.decode("ascii")
    if name == "q":
        stack.append(Style(style.stroke, style.fill, style.width, style.dash))
    elif name == "Q":
        if stack:
            style = stack.pop()
    elif name == "RG":
        style.stroke = tuple(map(f, args))
    elif name == "rg":
        style.fill = tuple(map(f, args))
    elif name == "G":
        style.stroke = tuple(map(f, args))
    elif name == "g":
        style.fill = tuple(map(f, args))
    elif name == "K":
        style.stroke = tuple(map(f, args))
    elif name == "k":
        style.fill = tuple(map(f, args))
    elif name == "w":
        style.width = f(args[0])
    elif name == "d":
        style.dash = (tuple(map(f, args[0])), f(args[1]))
    elif name == "m":
        current.append(point(cm, f(args[0]), f(args[1])))
    elif name == "l":
        current.append(point(cm, f(args[0]), f(args[1])))
    elif name == "c":
        current.extend(
            [
                point(cm, f(args[0]), f(args[1])),
                point(cm, f(args[2]), f(args[3])),
                point(cm, f(args[4]), f(args[5])),
            ]
        )
    elif name == "v":
        current.extend(
            [
                point(cm, f(args[0]), f(args[1])),
                point(cm, f(args[2]), f(args[3])),
            ]
        )
    elif name == "y":
        current.extend(
            [
                point(cm, f(args[0]), f(args[1])),
                point(cm, f(args[2]), f(args[3])),
            ]
        )
    elif name == "re":
        x, y, w, h = map(f, args)
        current.extend([point(cm, x, y), point(cm, x + w, y), point(cm, x + w, y + h), point(cm, x, y + h)])
    elif name in {"S", "s", "f", "f*", "B", "B*", "b", "b*"}:
        if current:
            xs = [p[0] for p in current]
            ys = [p[1] for p in current]
            bbox = (min(xs), min(ys), max(xs), max(ys))
            sequence += 1
            paths.append(
                PaintedPath(
                    sequence,
                    name,
                    bbox,
                    len(current),
                    Style(style.stroke, style.fill, style.width, style.dash),
                    tuple(current),
                )
            )
        current = []
    elif name == "n":
        current = []


def main() -> None:
    page = PdfReader(PDF).pages[690]
    page.extract_text(visitor_operand_before=visitor)
    print(f"TOTAL_PAINTED_PATHS={len(paths)}")
    selected = [p for p in paths if p.bbox[2] >= 90 and p.bbox[0] <= 510 and p.bbox[3] >= 130 and p.bbox[1] <= 300]
    print(f"FIGURE_REGION_PATHS={len(selected)}")
    for p in selected:
        print(
            p.sequence,
            p.paint_op,
            tuple(round(v, 3) for v in p.bbox),
            "points=", p.point_count,
            "stroke=", tuple(round(v, 4) for v in p.style.stroke),
            "fill=", tuple(round(v, 4) for v in p.style.fill),
            "width=", round(p.style.width, 4),
            "dash=", p.style.dash,
            "points_list=", tuple((round(x, 3), round(y, 3)) for x, y in p.points),
        )


if __name__ == "__main__":
    main()
