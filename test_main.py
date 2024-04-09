# pylint: disable=E1101
from main import get_main_concepts, get_totales, get_bases


INPUT = "example.pdf"

from main import _get_lines
for line in _get_lines(INPUT):
    print(line)

def test_main_concepts():
    out = get_main_concepts(INPUT)

    for field in out.__dataclass_fields__:
        v = getattr(out, field)
        assert len(v) == 15
        if field == "concepto" or field == "codigo":
            continue
        assert _check_all_are_floats_or_none(v)
        assert any([x for x in v if x is not None])


def test_totales():
    out = get_totales(INPUT)

    for field in out.__dataclass_fields__:
        v = getattr(out, field)
        assert v > 0
        assert isinstance(v, float)
    assert out.devengos - out.deducciones == out.liquido_a_recibir


def test_all():
    main = get_main_concepts(INPUT)
    totales = get_totales(INPUT)

    assert round(sum(filter(None, main.devengos)), 2) == totales.devengos
    assert round(sum(filter(None, main.deducciones)), 2) == totales.deducciones

def test_get_bases():
    out = get_bases(INPUT)

    assert len(out.calculo_bases) == 3
    assert len(out.contin_comunes) == 3
    assert len(out.accidentes) == 3
    assert len(out.irpf) == 3
    
    assert _check_all_are_floats_non_zero(out.contin_comunes)
    assert _check_all_are_floats_non_zero(out.accidentes)
    assert _check_all_are_floats_non_zero(out.irpf)

def _check_all_are_floats_non_zero(lst):
    return all(isinstance(i, float) and i > 0 for i in lst)

def _check_all_are_floats_or_none(lst):
    return all((isinstance(i, float) and i > 0) or i is None for i in lst)
