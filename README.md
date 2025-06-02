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

### Convert the payslip into GNUCash compatible transactions

```
❯ python to_gnucash.py -h
usage: to_gnucash.py [-h] [--print_header] payslip_path income_account

Generate GNUCash CSV from payslip

positional arguments:
  payslip_path    Path to the payslip PDF file
  income_account  Account fullname where the payslip is received

options:
  -h, --help      show this help message and exit
  --print_header  Print the CSV header
```

The `to_gnucash.py` script converts a payslip into something like

```csv
Date,Description,Notes,Deposit,Account
2024-01-26,Nómina,Salario bruto,-4630.0,Ingresos:Sueldo
,,"Ticket Restaurante (Edenred), exento de IRPF",209.0,Ingresos:Pagas Extra:Ticket restaurante
,,Cotización en Seguridad Social,200,Gastos:Impuestos:Salario
,,Cotización en Desempleo,100,Gastos:Impuestos:Salario
,,Cotización en Formación profesional,5.0,Gastos:Impuestos:Salario
,,Cotización en MEI,5.0,Gastos:Impuestos:Salario
,,Retención IRPF,1000.0,Gastos:Impuestos:Salario
,,Impuestos sobre el seguro dental,3.0,Gastos:Impuestos:Salario
,,Impuestos por los Rewards,50.0,Gastos:Impuestos:Salario
,,Impuestos sobre el descuento de los ESPP,37.0,Gastos:Impuestos:Salario
,Total Income,,-2000.00,Activo:Bancos:Cuenta nómina
```

You can configure the mapping of the payslip concepts to the GNUCash accounts
using the [configuration.csv](configuration.csv). You can also configure the
day of the transaction and the description in the code constants.

Once everything is set up, you can run

```
python to_gnucash.py payslips/2024_01.pdf "Activo:Bancos:Cuenta nómina" --print_header
```

to generate the CSV in the stdout. You can also do a bulk processing like:

```
echo "Date,Description,Notes,Deposit,Account" > out.csv
for file in payslips/*;
do python to_gnucash.py "$file" "Activo:Bancos:Cuenta nómina";
done >> out.csv
```

You can then insert in GNUCash:

```
python insert_in_gnucash.py out.csv $MY_BOOK.gnucash
```

Make sure the book is in sqlite3 format!
