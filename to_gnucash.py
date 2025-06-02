"""
This script takes a paylsip (in PDF) and generates a GNUCash compatible
CSV with a single transaction and multiple splits.

You may need to tweak the configuration.csv in order to adjust to your
accounts.
"""

import pandas as pd
import datetime
import logging
import argparse

from main import get_main_concepts, get_totales
from all_together import _split_concepto


logger = logging.getLogger(__name__)

# the payslip doesn't match the actual day the transfer is done to the bank
DAY_RECEIVED = 26
GNUCASH_TRANSACTION_DESCRIPTION = "Ingreso de nómina"


def get_date(payslip: str, day: int = DAY_RECEIVED) -> datetime.date:
    year, month = payslip.split("/")[-1].removesuffix(".pdf").split("_")
    logger.debug(f"Payslip date is {month}/{year}")
    return datetime.date(int(year), int(month), DAY_RECEIVED)


def load_configuration(path: str = "configuration.csv") -> pd.DataFrame:
    config_df = pd.read_csv(path)

    # Define expected columns based on configuration.csv
    expected_columns = [
        "code",
        "concept",
        "description",
        "account",
        "ignore",
        "why",
        "warn",
    ]

    # Check if all expected columns exist in the DataFrame
    missing_columns = [col for col in expected_columns if col not in config_df.columns]

    if missing_columns:
        raise ValueError(
            f"Missing required columns in configuration.csv: {missing_columns}"
        )
    logger.info("Configuration loaded")
    return config_df


def validate_code_and_concept(row: pd.Series, config_df: pd.DataFrame):
    """This is more like a validation for the configuration.

    Make sure that the code and concept matches both in the configuration and
    the payslip, as we will be using the code to create the splits."""
    codigo = row["codigo"]
    concepto = row["concepto"].strip()

    match_found = (
        (config_df["code"] == codigo) & (config_df["concept"] == concepto)
    ).any()

    if not match_found:
        raise ValueError(
            f"No match found in configuration for codigo: {codigo}, concept: {concepto}"
        )

    return match_found  # Return the boolean result


def check_for_warns(main_concepts_df: pd.DataFrame, config_df: pd.DataFrame):
    warnings = config_df[config_df["warn"]]["code"].values
    if len(main_concepts_df[main_concepts_df["codigo"].isin(warnings)]) > 0:
        logger.warning(
            f"This payslip may need a special treatment:\n{main_concepts_df}"
        )


def remove_columns_to_be_ignored(
    main_concepts_df: pd.DataFrame, config_df: pd.DataFrame
):
    # Filter out rows from main_concepts_df based on the 'ignore' column in config_df
    ignored_codes = config_df[config_df["ignore"]]["code"].values
    out = main_concepts_df[~main_concepts_df["codigo"].isin(ignored_codes)]
    logger.info("Rows with ignored codes have been removed")
    return out


def process_payslip_concepts(
    payslip_path: str, config_df: pd.DataFrame
) -> pd.DataFrame:
    """Processes the payslip PDF and extracts the main concepts."""
    main_concepts = get_main_concepts(payslip_path)
    logger.info("Main concepts calculated")

    main_concepts_df = pd.DataFrame(main_concepts.__dict__)
    _split_concepto(main_concepts_df)

    # Apply the validation function to each row and store the result in a new column
    main_concepts_df.apply(
        lambda row: validate_code_and_concept(row, config_df), axis=1
    )
    check_for_warns(main_concepts_df, config_df)
    main_concepts_df = remove_columns_to_be_ignored(main_concepts_df, config_df)

    # Convert 'concepto_extra' to string, replace comma with dot, and convert to numeric
    main_concepts_df["concepto_extra"] = (
        main_concepts_df["concepto_extra"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )
    main_concepts_df["concepto_extra"] = pd.to_numeric(
        main_concepts_df["concepto_extra"], errors="coerce"
    )

    logger.debug("Main concepts:")
    logger.debug(main_concepts_df)
    return main_concepts_df


def generate_gnucash_splits(
    main_concepts_df: pd.DataFrame,
    config_df: pd.DataFrame,
    payslip_path: str,
    income_account: str,
) -> pd.DataFrame:
    """Generates GNUCash compatible splits from processed payslip concepts."""
    splits_list = []
    total = 0

    for _, row in main_concepts_df.iterrows():
        match = config_df[(config_df["code"] == row["codigo"])]
        if match.empty:
            raise ValueError(f"No match found for:\n{row}")

        description = match["description"].values[0]
        account = match["account"].values[0]
        deposit = None

        if "devengos" in row and not pd.isna(row["devengos"]):
            deposit = -row["devengos"]
            total += deposit
        elif "deducciones" in row and not pd.isna(row["deducciones"]):
            deposit = row["deducciones"]
            total += deposit
        elif "concepto_extra" in row and not pd.isna(row["concepto_extra"]):
            deposit = row["concepto_extra"]
            # total += deposit not here because it's an extra pay
        else:
            raise ValueError(
                f"No valid value found for deposit/deduction in row:\n{row}"
            )

        splits_list.append(
            {
                "Date": None,
                "Description": None,
                "Notes": description,
                "Deposit": deposit,
                "Account": account,
            }
        )

    total = round(total, 2)

    # Create the DataFrame from the list of splits
    splits_df = pd.DataFrame(splits_list)

    # add the date just to the first row, this way it's treated as a single transaction with multiple splits
    # Use .loc with row and column specifiers together to avoid SettingWithCopyWarning
    payslip_date = get_date(payslip_path)
    logger.info(f"Payslip date is: {payslip_date}")
    splits_df.loc[0, "Date"] = payslip_date
    splits_df.loc[0, "Description"] = GNUCASH_TRANSACTION_DESCRIPTION

    totals = get_totales(payslip_path)
    assert (
        totals.liquido_a_recibir == -total
    ), f"Got a difference in the total income for\n{splits_df}\nExpected {totals.liquido_a_recibir} but got {-total}"

    total_income_row = {
        "Date": None,
        "Description": None,
        "Notes": "Salario neto recibido en la cuenta del banco",
        "Deposit": -total,
        "Account": income_account,
    }
    splits_df = pd.concat(
        [splits_df, pd.DataFrame([total_income_row])], ignore_index=True
    )

    logger.debug(splits_df)

    # clean up (remove rows with NaN accounts)
    splits_df = splits_df[~pd.isna(splits_df["Account"])]
    logger.debug("Splits:")
    return splits_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Generate GNUCash CSV from payslip")
    parser.add_argument("payslip_path", help="Path to the payslip PDF file")
    parser.add_argument(
        "income_account", help="Account fullname where the payslip is received"
    )
    parser.add_argument(
        "--print_header", action="store_true", help="Print the CSV header"
    )

    args = parser.parse_args()

    payslip_path = args.payslip_path
    income_account = args.income_account

    config_df = load_configuration()
    main_concepts_df = process_payslip_concepts(payslip_path, config_df)
    splits_df = generate_gnucash_splits(
        main_concepts_df, config_df, payslip_path, income_account
    )

    print(splits_df.to_csv(index=False, header=args.print_header))
