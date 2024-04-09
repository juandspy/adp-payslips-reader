# Payslip reader

Download the payslips from ADP as a ZIP file and then run

```sh
for file in payslips/*; do mv "$file" "payslips/$(basename $file | cut -d'_' -f 2,3).pdf"; done
```

in order to have a folder containing all the payslips you want to analyze.

Run `python all_together.py` in order to join all your payslips in a set of
CSV files under the `output` folder.
