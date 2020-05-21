#!/usr/bin/python3
"""
Because SoFi does not have a way to export transactions, I built this script to
parse their PDF statements
"""

import re
import os
import csv
from datetime import datetime

from tika import unpack


STATEMENTS_FOLDER = os.environ.get("STATEMENTS_FOLDER", "Statements")
TRANSACTIONS_FOLDER = os.environ.get("TRANSACTIONS_FOLDER", "Transactions")

TRANSACTIONS_HEADER = "DATE TYPE DESCRIPTION AMOUNT BALANCE"

output_dirs = None

# Potentially could get any of this data and more from the PDF
# but I just want the transactions
keywords = [
    "Primary Account Holder",
    "Member since",
    "Account Number",
    "Monthly Statement Period",
    "Current Balance",
    "Current Interest Rate",
    "Interest Rate Earned This Period",
    "Monthly Interest Paid",
    "Beginning Balance",
    "APY Earned This Period",
    "Year-to-date Interest Paid",
    "Transaction Details",
    TRANSACTIONS_HEADER,
    "Contact Information",
    "Sweep Program Details",
]


for root, dirs, files in os.walk(STATEMENTS_FOLDER):

    if not output_dirs:

        # Make transaction dirs if they don't exist
        # * I have my statements saved in sub dirs by year so this creates those
        output_dirs = sorted([f"{TRANSACTIONS_FOLDER}/{d}" for d in dirs])
        for transaction_dir in output_dirs:
            if not os.path.isdir(transaction_dir):
                os.makedirs(transaction_dir)

    if files:
        for filename in files:
            path = f"{root}/{filename}"
            if os.path.splitext(path)[1] == ".pdf":
                contents = unpack.from_file(path).get("content", "")
                iterator = iter(re.split(f"({'|'.join(keywords)})", contents))

                file_data = []

                for key in iterator:
                    if key in keywords:

                        try:
                            value = next(iterator)

                            if key == TRANSACTIONS_HEADER:

                                # Split by the date format: "Jan 1, 1970"
                                # or 2 new lines
                                split = re.split(
                                    r"(\w{3} \d{1,2}, 20\d{2})|\n\n", value,
                                )

                                # Clean up whitespace and empty strings in list
                                page_data = [
                                    val.replace("\n", " ").strip()
                                    for val in split
                                    if val
                                ]

                                # Convert stream of parsed data to 3 column rows
                                page_data = [
                                    list(entry)
                                    for entry in zip(*[iter(page_data)] * 3)
                                    if entry
                                ]

                                for row in page_data:

                                    # Convert date format
                                    date = datetime.strptime(row[0], "%b %d, %Y")
                                    row[0] = datetime.strftime(date, "%d/%m/%Y")

                                    # Cleanup description
                                    row[1] = " ".join(row[1].split())

                                    # split amount / balance and cleanup
                                    amount, balance = row[2].split()
                                    row[2] = float(
                                        amount.replace("$", "").replace(",", "")
                                    )
                                    row.append(
                                        float(balance.replace("$", "").replace(",", ""))
                                    )
                                    file_data.append(row)

                        except StopIteration:
                            pass

                output_filename = (
                    os.path.splitext(path)[0].replace(
                        STATEMENTS_FOLDER, TRANSACTIONS_FOLDER
                    )
                    + ".csv"
                )

                # Write and read the files
                if file_data:
                    with open(output_filename, "w") as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerows(file_data)
                    with open(output_filename, "r") as csv_file:
                        print(output_filename)
                        print(csv_file.read())
