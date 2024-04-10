import pandas as pd
import os
import datetime
from typing import List, Tuple
from io import BytesIO

from main import get_bases, get_main_concepts, get_totales


def _split_concepto(df: pd.DataFrame):
    # there are some concepts with some values
    new_cols = df['concepto'].str.extract(
        '([a-zA-Z\s\.]+)([\d\.,]+)?').fillna('').values.T

    col_index = df.columns.get_loc('concepto')
    df["concepto"] = new_cols[0]
    df.insert(col_index + 1, 'concepto_extra', new_cols[1])


def join(payslips: List[str | BytesIO], filenames: List[str] = []) -> Tuple[pd.DataFrame]:
    main_concepts_df = pd.DataFrame()
    bases_df = pd.DataFrame()
    totales_df = pd.DataFrame()

    for i, payslip in enumerate(payslips):
        if isinstance(payslip, str):
            year, month = payslip.split("/")[-1].removesuffix(".pdf").split("_")
        elif isinstance(payslip, BytesIO):
            year, month = filenames[i].split("/")[-1].removesuffix(".pdf").split("_")
        else:
            raise ValueError(f"{payslip} has an unsupported format: {type(payslip)}")
        date = datetime.date(int(year), int(month), 1)

        # main concepts
        main_concepts = get_main_concepts(payslip)

        df = pd.DataFrame(main_concepts.__dict__)
        df["date"] = pd.to_datetime(date).strftime('%m/%Y')
        df = df.set_index("date")
        _split_concepto(df)

        main_concepts_df = pd.concat([main_concepts_df, df])

        # bases
        bases = get_bases(payslip)
        df = pd.DataFrame(bases.__dict__)
        df["date"] = pd.to_datetime(date).strftime('%m/%Y')
        df = df.set_index("date")

        bases_df = pd.concat([bases_df, df])

        # totales
        totales = get_totales(payslip)
        df = pd.DataFrame(totales.__dict__, index=[0])
        df["date"] = pd.to_datetime(date).strftime('%m/%Y')
        df = df.set_index("date")

        totales_df = pd.concat([totales_df, df])

    main_concepts_df = main_concepts_df.sort_index()

    bases_df = bases_df.sort_index()

    totales_df = totales_df.sort_index()

    return main_concepts_df, bases_df, totales_df

if __name__ == "__main__":
    PAYSLIPS_FOLDER = "payslips"
    OUTPUT_FOLDER = "output"
    payslips = [f"{PAYSLIPS_FOLDER}/{x}" for x in os.listdir("payslips")
                if x.endswith(".pdf")]

    main_concepts_df, bases_df, totales_df = join(payslips)

    main_concepts_df.to_csv(f"{OUTPUT_FOLDER}/main_concepts.csv")
    bases_df.to_csv(f"{OUTPUT_FOLDER}/bases.csv")
    totales_df.to_csv(f"{OUTPUT_FOLDER}/totales.csv")
