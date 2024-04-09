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

    def parse_line(line: str) -> Tuple[int, str, float, float, float, float]:
        code_and_concept = line[:29]

        codigo = _parse_int(code_and_concept[:4])
        concepto = code_and_concept[4:]
        cantidad_o_base = _parse_float(line[29:40])
        precio_uni = _parse_float(line[40:53])
        devengos = _parse_float(line[53:67])
        deducciones = _parse_float(line[67:])

        return codigo, concepto, cantidad_o_base, \
            precio_uni, devengos, deducciones

    out = MainConcepts()

    parse = False
    for line in _get_lines(filepath):
        # Ignore all lines until one that contains "SALARIO BASE"
        if "SALARIO BASE" in line:
            parse = True

        # Then parse each line until a blank line is found
        if not parse:
            continue
        if not re.search('[a-zA-Z0-9]', line):
            break
        codigo, concepto, cantidad_o_base, precio_uni, devengos, deducciones = parse_line(line)

        out.codigo.append(codigo)
        out.concepto.append(concepto)
        out.cantidad_o_base.append(cantidad_o_base)
        out.precio_uni.append(precio_uni)
        out.devengos.append(devengos)
        out.deducciones.append(deducciones)
    return out


def get_totales(filepath: str) -> Totals:
    out = Totals()

    previous_non_empty_line = ""
    for line in _get_lines(filepath):
        if "LIQUIDO A RECIBIR" in line:
            out.liquido_a_recibir = _parse_float(line.replace("€", "").\
                replace(",", ".").replace("LIQUIDO A RECIBIR", ""))

            splitted = previous_non_empty_line.\
                strip().split(" ")
            out.devengos = _parse_float(splitted[0])
            out.deducciones = _parse_float(splitted[-1])

            return out
        if len(line.strip()) > 0:
            previous_non_empty_line = line

def get_bases(filepath: str) -> Bases:
    out = Bases()

    parse = False
    lines_to_parse = []
    previous_line = ""
    for line in _get_lines(filepath):
        if "****" in line:
            # The data is in the 5 next non empty lines after the bank account
            # and the line before!
            # The bank account is anonymized using some "*", so this is a dirty
            # trick to find the line
            parse = True
            lines_to_parse.append(previous_line)
            continue
        previous_line = line
        if not parse:
            continue
        if len(lines_to_parse) == 6:
            break
        if len(line.strip()) == 0:
            continue
        lines_to_parse.append(line)

    out.calculo_bases = ["REMUNERACION PRORRATEO", "TOTAL", "BASE NORMALIZ."]
    out.contin_comunes = [
        _parse_float(x) for x in lines_to_parse[0].split('Banco')[0]\
            .split(" ") if x != ""]
    out.accidentes = [
        _parse_float(x) for x in lines_to_parse[1].split(" ") if x != ""]
    out.irpf = [
        _parse_float(x) for x in lines_to_parse[2].split(" ") if x != ""]
    out.acu_base_irpf = _parse_float(lines_to_parse[3])
    out.acu_irpf = _parse_float(lines_to_parse[4])
    out.acu_cotiz_ss = _parse_float(lines_to_parse[5])
    return out

def _parse_int(s: str) -> int | None:
    return int(s.strip())

def _parse_float(s: str) -> float | None:
    if len(s.strip()) == 0:
        return None
    return round(float(s.replace(",", ".").strip()), 2)


if __name__ == "__main__":
    filepath = os.environ.get("FILE_PATH", "example.pdf")
    print(get_main_concepts(filepath))
    print(get_totales(filepath))
    print(get_bases(filepath))
