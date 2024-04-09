"""TODO"""

from typing import Dict, List, Tuple
from pypdf import PdfReader
from dataclasses import dataclass, field
import os
import re

@dataclass
class MainConcepts:
    codigo: List[int] = field(default_factory=list)
    concepto: List[str] = field(default_factory=list)
    cantidad_o_base: List[float] = field(default_factory=list)
    precio_uni: List[float] = field(default_factory=list)
    devengos: List[float] = field(default_factory=list)
    deducciones: List[float] = field(default_factory=list)

@dataclass
class Totals:
    devengos: float | None = None
    deducciones: float | None = None
    liquido_a_recibir: float | None = None

@dataclass
class Bases:
    calculo_bases: List[str] = field(default_factory=list)
    contin_comunes: List[float] = field(default_factory=list)
    accidentes: List[float] = field(default_factory=list)
    irpf: List[float] = field(default_factory=list)

    acu_base_irpf: float = None
    acu_irpf: float = None
    acu_cotiz_ss: float = None


def _get_lines(filepath: str, page: int = 0) -> str:
    reader = PdfReader(filepath)
    page = reader.pages[page]
    return page.extract_text().split("\n")

def get_main_concepts(filepath: str) -> MainConcepts:
    """Get the concepts from the main table."""

    def parse_line(line: str, _format: str = "new") -> Tuple[int, str, float, float, float, float]:
        code_and_concept = line[:29]

        codigo = _parse_int(code_and_concept[:4])
        concepto = code_and_concept[4:]
        cantidad_o_base = _parse_float(line[29:40], 1 if parse_format == "new" else 1000)
        precio_uni = _parse_float(line[40:53], 1 if parse_format == "new" else 10000)
        devengos = _parse_float(line[53:63], 1 if parse_format == "new" else 100)
        deducciones = _parse_float(line[63:], 1 if parse_format == "new" else 100)

        return codigo, concepto, cantidad_o_base, \
            precio_uni, devengos, deducciones

    out = MainConcepts()

    parse = False
    parse_format = "new"
    lines = _get_lines(filepath)
    if "TRANSFERENCIA" in "".join(lines):
        parse_format = "old"
    for line in lines:
        # Ignore all lines until one that contains "SALARIO BASE"
        if "SALARIO BASE" in line:
            parse = True

        # Then parse each line until a blank line is found
        if not parse:
            continue
        if not re.search('[a-zA-Z0-9]', line):
            break
        codigo, concepto, cantidad_o_base, precio_uni, devengos, deducciones = parse_line(line, parse_format)

        out.codigo.append(codigo)
        out.concepto.append(concepto)
        out.cantidad_o_base.append(cantidad_o_base)
        out.precio_uni.append(precio_uni)
        out.devengos.append(devengos)
        out.deducciones.append(deducciones)
    return out


def get_totales(filepath: str) -> Totals:
    out = Totals()

    line_with_totals = ""
    lines = _get_lines(filepath)
    divide_by = 1

    for i, line in enumerate(lines):
        if "LIQUIDO A RECIBIR" in line:
            out.liquido_a_recibir = _parse_float(line.replace("€", "").\
                replace(",", ".").replace("LIQUIDO A RECIBIR", ""))
            line_with_totals = lines[i - 1]
            break

        if "TRANSFERENCIA" in line:
            out.liquido_a_recibir = _parse_float(lines[i - 2])
            line_with_totals = lines[i - 5]
            divide_by = 100
    splitted = line_with_totals.strip().split(" ")
    out.devengos = _parse_float(splitted[0], divide_by)
    out.deducciones = _parse_float(splitted[-1], divide_by)
    return out


def get_bases(filepath: str) -> Bases:
    out = Bases()

    lines_to_parse = []
    lines = _get_lines(filepath)

    for i, line in enumerate(lines):
        if "TRANSFERENCIA" in line:
            lines_to_parse.append(lines[i-1])
            lines_to_parse.extend(lines[i+2:i+11])
        if "****" in line:
            # The data is in the 5 next non empty lines after the bank account
            # and the line before!
            # The bank account is anonymized using some "*", so this is a dirty
            # trick to find the line
            lines_to_parse.append(lines[i-1])
            lines_to_parse.extend(lines[i+2:i+11])
            break

    lines_to_parse = [line for line in lines_to_parse if len(line.strip()) != 0]
    out.calculo_bases = ["REMUNERACION PRORRATEO", "TOTAL", "BASE NORMALIZ."]

    remuneracion_prorrateo = [x for x in lines_to_parse[0].split(" ") if x != ""]
    out.contin_comunes.append(_parse_float(remuneracion_prorrateo[0]))
    out.accidentes.append(_parse_float(remuneracion_prorrateo[1]))
    out.irpf.append(_parse_float(remuneracion_prorrateo[2]))

    total = [_parse_float(x) for x in lines_to_parse[1].split(" ") if x != ""]
    out.contin_comunes.append(total[0])
    out.accidentes.append(total[1])
    out.irpf.append(total[2])

    base_normaliz = [x for x in lines_to_parse[2].split(" ") if x != ""]
    out.contin_comunes.append(_parse_float(base_normaliz[0]))
    out.accidentes.append(_parse_float(base_normaliz[1]))
    out.irpf.append(_parse_float(base_normaliz[2]))

    out.acu_base_irpf = _parse_float(lines_to_parse[3])
    out.acu_irpf = _parse_float(lines_to_parse[4])
    out.acu_cotiz_ss = _parse_float(lines_to_parse[5])

    return out

def _parse_int(s: str) -> int | None:
    return int(s.strip())

def _parse_float(s: str, divide_by:int = 1) -> float | None:
    # in the old format there are no decimals, so we need to divide by 100, 1000 or 10000 depending on the column
    if len(s.strip()) == 0:
        return None
    return round(float(s.replace(",", ".").strip()) / divide_by, 2)



if __name__ == "__main__":
    filepath = os.environ.get("FILE_PATH", "payslips/2023_01.pdf")
    print(get_main_concepts(filepath))
    print(get_totales(filepath))
    print(get_bases(filepath))
