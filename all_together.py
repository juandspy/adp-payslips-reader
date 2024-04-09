import pandas as pd
import os
import datetime

from main import get_bases, get_main_concepts, get_totales


PAYSLIPS_FOLDER = "payslips"
OUTPUT_FOLDER = "output"

main_concepts_df = pd.DataFrame()
bases_df = pd.DataFrame()
totales_df = pd.DataFrame()

for payslip in os.listdir("payslips"):
    year, month = payslip.removesuffix(".pdf").split("_")
    date = datetime.date(int(year), int(month), 1)

    # main concepts
    main_concepts = get_main_concepts(filepath=f"{PAYSLIPS_FOLDER}/{payslip}")

    df = pd.DataFrame(main_concepts.__dict__)
    df["date"] = pd.to_datetime(date)
    df = df.set_index("date")

    main_concepts_df = pd.concat([main_concepts_df, df])

    # bases
    bases = get_bases(filepath=f"{PAYSLIPS_FOLDER}/{payslip}")
    df = pd.DataFrame(bases.__dict__)
    df["date"] = pd.to_datetime(date)
    df = df.set_index("date")

    bases_df = pd.concat([bases_df, df])

    # totales
    totales = get_totales(filepath=f"{PAYSLIPS_FOLDER}/{payslip}")
    df = pd.DataFrame(totales.__dict__, index=[0])
    df["date"] = pd.to_datetime(date)
    df = df.set_index("date")

    totales_df = pd.concat([totales_df, df])

main_concepts_df = main_concepts_df.sort_index()
main_concepts_df.to_csv(f"{OUTPUT_FOLDER}/main_concepts.csv")

bases_df = bases_df.sort_index()
bases_df.to_csv(f"{OUTPUT_FOLDER}/bases.csv")

totales_df = totales_df.sort_index()
totales_df.to_csv(f"{OUTPUT_FOLDER}/totales.csv")
