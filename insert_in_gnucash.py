"""
This script takes a paylsip (in PDF) and generates a GNUCash compatible
CSV with a single transaction and multiple splits.

You may need to tweak the configuration.csv in order to adjust to your
accounts.
"""

import pandas as pd
import piecash
import logging
import argparse
import warnings
from sqlalchemy import exc as sa_exc
from datetime import datetime
from decimal import Decimal, getcontext


logger = logging.getLogger(__name__)


def check_columns(csv_data: pd.DataFrame):
    required_columns = ["Date", "Description", "Notes", "Deposit", "Account"]
    if not all(col in csv_data.columns for col in required_columns):
        raise ValueError("CSV does not contain all required columns")


def check_accounts(csv_data: pd.DataFrame, book: piecash.Book):
    csv_accounts = csv_data["Account"].unique()
    missing_accounts = [
        account
        for account in csv_accounts
        if account not in [account.fullname for account in book.accounts]
    ]
    if missing_accounts:
        raise ValueError(f"Missing accounts in the book: {missing_accounts}")


def insert_transactions(csv_data: pd.DataFrame, book: piecash.Book):
    """
    Inserts transactions from the CSV data into the GnuCash book.
    Assumes rows with the same Date and Description belong to the same transaction.
    """
    logger.info("Inserting transactions into the book...")

    transaction_currency = book.default_currency

    current_transaction = None
    for i, row in csv_data.iterrows():
        # If there's a date, it's the start of a new transaction
        if not pd.isna(row["Date"]):
            # If there was a previous transaction, add it to the book
            if current_transaction:
                if sum(split.value for split in current_transaction.splits) != 0:
                    total = 0
                    for split in current_transaction.splits:
                        total += split.value
                        print(split, split.value)
                    print(total)
                    raise ValueError("Sum of splits is not 0")
                book.add(current_transaction)

            # Start a new transaction
            transaction_date = pd.to_datetime(row["Date"]).date()
            transaction_description = row["Description"]
            current_transaction = piecash.Transaction(
                currency=transaction_currency,
                description=transaction_description,
                post_date=transaction_date,
                enter_date=datetime.now(),
                splits=[],  # Initialize with an empty splits list
            )

        # Add the split to the current transaction
        if current_transaction is not None:  # Ensure current_transaction is not None
            current_transaction.splits.append(
                piecash.Split(
                    account=book.accounts(fullname=row["Account"]),
                    value=round(Decimal(row["Deposit"]), 2),
                    memo=row["Notes"],
                )
            )
        else:
            # This case should ideally not happen if the first row has a date
            # but adding a safeguard or a warning might be good.
            logger.warning(
                f"Skipping row {i} as it has no date and no active transaction."
            )

    # Add the last transaction after the loop finishes
    if current_transaction:
        book.add(current_transaction)

    logger.info("Transactions added. Saving book...")
    book.save()
    logger.info("Book saved.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Insert a CSV in GNUCash")
    parser.add_argument("csv_path", help="Path to the CSV with the transactions")
    parser.add_argument("gnucash_path", help="Path to the GNUCash book")
    # The book must be in sqlite format!

    args = parser.parse_args()

    csv_data = pd.read_csv(args.csv_path, dtype={"Deposit": "float64"})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        book = piecash.open_book(args.gnucash_path, readonly=False)

    check_columns(csv_data)
    check_accounts(csv_data, book)

    # Call the new function to insert transactions
    insert_transactions(csv_data, book)
