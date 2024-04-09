# pylint: disable=E1101
import pytest
import os

from main import get_main_concepts, get_totales, get_bases

MAIN_MAXIMUM_VALUE = 15000
BASES_MAXIMUM_VALUE = 200000
MIN_NUM_OF_CONCEPTS = 8
PAYSLIPS_FOLDER = "payslips"

@pytest.mark.parametrize("test_input", [
    (f"{PAYSLIPS_FOLDER}/{x}") for x in os.listdir(PAYSLIPS_FOLDER)])
class TestAllFormats:

    def test_main_concepts(self, test_input):
        out = get_main_concepts(test_input)

        for field in out.__dataclass_fields__:
            v = getattr(out, field)
            assert len(v) > MIN_NUM_OF_CONCEPTS
            if field == "concepto" or field == "codigo":
                continue
            assert _check_all_are_floats_or_none(v)
            assert any([x for x in v if x is not None])
            assert _check_all_lower_than(v, MAIN_MAXIMUM_VALUE)


    def test_totales(self, test_input):
        out = get_totales(test_input)

        for field in out.__dataclass_fields__:
            v = getattr(out, field)
            assert v > 0
            assert isinstance(v, float)
            assert _check_all_lower_than([v], MAIN_MAXIMUM_VALUE)
        assert round(out.devengos - out.deducciones, 2) == round(out.liquido_a_recibir, 2)


    def test_all(self, test_input):
        main = get_main_concepts(test_input)
        totales = get_totales(test_input)

        assert round(sum(filter(None, main.devengos)), 2) == round(totales.devengos, 2)
        assert round(sum(filter(None, main.deducciones)), 2) == round(totales.deducciones, 2)

    def test_get_bases(self, test_input):
        out = get_bases(test_input)

        assert len(out.calculo_bases) == 3
        for v in [out.contin_comunes, out.accidentes, out.irpf]:
            assert len(v) == 3
            assert _check_all_are_floats_non_zero(v)
            assert _check_all_lower_than(v, BASES_MAXIMUM_VALUE)

def _check_all_are_floats_non_zero(lst):
    return all(isinstance(i, float) and i > 0 for i in lst)

def _check_all_are_floats_or_none(lst):
    return all((isinstance(i, float) and i > 0) or i is None for i in lst)

def _check_all_lower_than(lst, target):
    for i in lst:
        if i is None:
            continue
        if i > target:
            return False
    return True
