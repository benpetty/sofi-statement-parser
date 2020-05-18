#!/usr/bin/python3
"""
Because SoFi does not have a way to export transactions, I built this script to
parse their PDF statements
"""

import re
import os
import csv
import json
from datetime import datetime

from tika import unpack


STATEMENTS_FOLDER = os.environ.get("STATEMENTS_FOLDER", "Statements")
TRANSACTIONS_FOLDER = os.environ.get("TRANSACTIONS_FOLDER", "Transactions")

TRANSACTIONS_HEADER = "DATE TYPE DESCRIPTION AMOUNT BALANCE"

output_dirs = None
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
        output_dirs = sorted([f"{TRANSACTIONS_FOLDER}/{d}" for d in dirs])
        # Make transaction dirs if they don't exist
        for transaction_dir in output_dirs:
            if not os.path.isdir(transaction_dir):
                os.makedirs(transaction_dir)

    if files:
        for filename in files:
            path = f"{root}/{filename}"
            if os.path.splitext(path)[1] == ".pdf":
                contents = unpack.from_file(path).get("content", "")
                iterator = iter(re.split(f"({'|'.join(keywords)})", contents))

                for key in iterator:
                    if key in keywords:

                        try:
                            value = next(iterator)

                            if key == TRANSACTIONS_HEADER:
                                split = re.split(
                                    r"(\w{3} \d{1,2}, 20\d{2})|\n\n", value,
                                )
                                data = [
                                    val.replace("\n", " ").strip()
                                    for val in split
                                    if val
                                ]
                                data = [
                                    list(tup) for tup in zip(*[iter(data)] * 3) if tup
                                ]

                                for row in data:

                                    # Convert date format
                                    try:
                                        date = datetime.strptime(row[0], "%b %d, %Y")
                                        row[0] = datetime.strftime(date, "%d/%m/%Y")
                                    except ValueError:
                                        del row

                                    # Cleanup description
                                    row[1] = " ".join(row[1].split())

                                    # split amount / balance
                                    amount, balance = row[2].split()
                                    row[2] = float(
                                        amount.replace("$", "").replace(",", "")
                                    )
                                    row.append(
                                        float(balance.replace("$", "").replace(",", ""))
                                    )

                        except StopIteration:
                            pass

                output_filename = (
                    os.path.splitext(path)[0].replace(
                        STATEMENTS_FOLDER, TRANSACTIONS_FOLDER
                    )
                    + ".csv"
                )

                if data:
                    with open(output_filename, "w") as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerows(data)

                    print("\n", output_filename)
                    print(json.dumps(data, indent=2))
