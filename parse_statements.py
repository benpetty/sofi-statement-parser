#!/usr/bin/python3
"""
Because SoFi does not have a way to export transactions, I built this script to
parse their PDF statements
"""

import re
import os
from datetime import datetime

from tika import unpack

TRANSACTION_ID = 'Transaction ID: '


output_dirs = None
keywords = [
    'Primary Account Holder',
    'Member since',
    'Account Number',
    'Monthly Statement Period',
    'Current Balance',
    'Current Interest Rate',
    'Interest Rate Earned This Period',
    'Monthly Interest Paid',
    'Beginning Balance',
    'APY Earned This Period',
    'Year-to-date Interest Paid',
    'Transaction Details',
    TRANSACTION_ID,
]


for root, dirs, files in os.walk("Statements"):

    if not output_dirs:
        output_dirs = sorted([f"Transactions/{d}" for d in dirs])
        # Make transaction dirs if they don't exist
        for transaction_dir in output_dirs:
            if not os.path.isdir(transaction_dir):
                os.makedirs(transaction_dir)

    if files:
        for filename in files:
            path = f"{root}/{filename}"
            if os.path.splitext(path)[1] == '.pdf':

                contents = unpack.from_file(path).get("content", "")
                split = re.split(f"({'|'.join(keywords)})", contents)

                data = []

                iterator = iter(split)

                for key in iterator:
                    if key in keywords:
                        try:
                            value = next(iterator)
                            if key == TRANSACTION_ID:
                                value = [val for val in value.split("\n")[:6] if val]
                                transaction_id = value[0]
                                amount = value[1].replace("$", "").split()[0]
                                balance = value[1].replace("$", "").split()[1]
                                date = ''.join(re.split(r'(\d{4})', value[2])[:2])
                                try:
                                    date = datetime.strftime(datetime.strptime(date, '%b %d, %Y'), '%m/%d/%Y')
                                    description = ''.join(re.split(r'(\d{4})', value[2])[2:]).strip()
                                except ValueError:
                                    description = date
                                    date = 'null'

                                value = ','.join([
                                    transaction_id,
                                    amount,
                                    balance,
                                    date,
                                    description,
                                ])
                                data.append((key, value))
                        except StopIteration:
                            pass

                output_filename = os.path.splitext(path)[0]
                print(f'\n{output_filename}.csv'.replace(root, 'Transactions'))
                for tup in data:
                    if tup[1]:
                        print(tup[1])
