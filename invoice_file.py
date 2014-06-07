#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import csv
import datetime
import collections
import sys

def indent(text):
    return '\n'.join([ '    ' + line for line in text.split('\n')])

class InvoiceFile(object):

    def __init__(self, file_name):
        self.file_name = file_name
        self.invoices = []

    def _add_invoice_from_row(self, row):
        invoice = Invoice.from_row(row)
        self.invoices.append(invoice)

    def _add_detail_to_last_invoice_from_row(self, row):
        try:
            last_invoice = self.invoices[-1]
        except IndexError:
            raise Exception('Detail without invoice', ''.join(row))
        last_invoice._add_detail_from_row(row)

    @classmethod
    def from_file(cls, file_name):
        invoice_file = cls(file_name)
        with open(file_name, 'rb') as csv_file:
            for raw_row in csv.reader(csv_file, delimiter='|'):
                row = [ field.decode('big5').encode('utf-8') for field in raw_row ]
                kind = row[0]
                if kind == 'M':
                    invoice_file._add_invoice_from_row(row)
                elif kind == 'D':
                    invoice_file._add_detail_to_last_invoice_from_row(row)
                else:
                    raise Exception('Unknown row type: ' + kind)
        return invoice_file

    def __repr__(self):
        text = '發票彙整 {0}（共 {1} 張發票）\n'.format(self.file_name, len(self.invoices))
        text += '\n'.join([ indent(invoice.__repr__()) for invoice in self.invoices ])
        return text

class Invoice(object):

    FIELDS = collections.OrderedDict([
        ('invoice_status', '發票狀態'),
        ('invoice_number', '發票號碼'),
        ('invoice_date',   '發票日期'),
        ('seller_id',      '商店統編'),
        ('seller_name',    '商店店名'),
        ('card_name',      '載具名稱'),
        ('card_id',        '載具號碼'),
        ('amount',         '總金額　'),
    ])

    def __init__(self, **keywords):
        for name in self.FIELDS:
            setattr(self, name, keywords[name])
        if self.invoice_status not in ['開立', '作廢']:
            raise Exception('Invalid invoice status: {0}, not in 開立 or 作廢'.format(self.invoice_status))
        self.details = []

    @classmethod
    def from_row(cls, row):
        # Remove invoice identifier
        if row[0] != "M":
            raise Exception("Invalid row kind for invoice: {0}, it should be M".format(row[0]))
        row = row[1:]
        # Unpack fields
        fields = dict(zip(cls.FIELDS, row))
        fields['invoice_date'] = datetime.datetime.strptime(fields['invoice_date'], '%Y%m%d')
        fields['seller_id'] = int(fields['seller_id'])
        fields['card_id'] = int(fields['card_id'])
        fields['amount'] = float(fields['amount'])
        # OK, create the object
        invoice = cls(**fields)
        return invoice

    def _add_detail_from_row(self, row):
        detail = Detail.from_row(row)
        if self.invoice_number != detail.invoice_number:
            raise Exception("Different invoice number: invoice: {0}, detail: {0}".format(
                                self.invoice_number,
                                detail.invoice_number))
        self.details.append(detail)

    def __repr__(self):
        text = '發票 {0}\n'.format(self.invoice_number)
        for name, description in self.FIELDS.items():
            text += '    {description}：{value}\n'.format(description=description, value=getattr(self, name))
        text += '    明細（共 {0} 項明細）\n'.format(len(self.details))
        text += '\n'.join([ indent(indent(detail.__repr__()))  for detail in self.details ])
        return text

class Detail(object):

    FIELDS = collections.OrderedDict([
        ('invoice_number', '發票號碼'),
        ('amount',         '小計'),
        ('description',    '品項名稱'),
    ])

    def __init__(self, **keywords):
        for name in self.FIELDS:
            setattr(self, name, keywords[name])

    @classmethod
    def from_row(cls, row):
        # Remove invoice identifier
        assert row[0] == "D"
        row = row[1:]
        # Unpack fields
        fields = dict(zip(cls.FIELDS, row))
        fields['amount'] = float(fields['amount'])
        # OK, create the object
        detail = cls(**fields)
        return detail

    def __repr__(self):
        text = '{description}：{value}\n'.format(description="名稱", value = self.description)
        text += '＄：{value}'.format(value = self.amount)
        return text

if __name__ == "__main__":

    map(print, map(InvoiceFile.from_file, sys.argv[1:]))

