# Payslip reader

A tool to parse ADP format payslips into CSVs.

## How to

### Check compatibility with your payslips

Download the payslips from ADP as a ZIP file and then run

```sh
for file in payslips/*; do mv "$file" "payslips/$(basename $file | cut -d'_' -f 2,3).pdf"; done
```

in order to have a folder containing all the payslips you want to analyze.

You can then run `pytest` or `python -m pytest` in order to check all those
payslips can be parsed by this tool. What the unit tests does is list all the
payslips in the `payslips` folder and make sure once they are parsed, the
quantities matches what the payslip says. For example, the sum of all
"devengos" must match the total "devengos".

### Join the payslips in a single CSV

Run `python all_together.py` in order to join all your payslips in a set of
CSV files under the `output` folder:

```
❯ ls output
bases.csv   main_concepts.csv   totales.csv
```

These files have an extra column with the date of the payslip.

- `bases.csv`: contains the values for the "bases de cotización"
- `main_concepts.csv`: contains the main concepts (ESPP, Bonus, salary...)
- `totales.csv`: gathers the total "devengos", "deducciones" and "total"
