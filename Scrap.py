from bs4 import BeautifulSoup
import pandas as pandass
import numpy as np
import requests
import datetime
from collections import defaultdict

#Code for assesing multiple rows in rowspan is insipired from an online link: 
#https://stackoverflow.com/questions/28763891/what-should-i-do-when-tr-has-rowspan
#first three methods only. Rest personal code
def process(table):
    len_all_rows = [y for y in table.find_all('tr')]
    rows = len(len_all_rows)

    len_all_cols = max([len(y.find_all(['th', 'td'])) for y in len_all_rows])
    main_rows = [z.find_all(['th', 'td']) for z in len_all_rows if len(z.find_all(['th', 'td'])) > len_all_cols / 2]
    main_cols = []

    for main_row in main_rows:
        len_all_cols = 0
        for csv in main_row:
            row, col = get_row_col(csv)
            len_all_cols += len([csv.getText()] * col)

        main_cols.append(len_all_cols)

    len_all_cols = max(main_cols)

    return (len_all_rows, rows, len_all_cols)


def get_row_col(csv):
    row=0
    col=9
    if csv.has_attr('rowspan'):
        row = int(csv.attrs['rowspan'])
    else:  
        row = 1
    if csv.has_attr('colspan'):
        col = int(csv.attrs['colspan'])
    else: 
        col = 1

    return (row, col)


def process_all(len_all_rows, rows, len_all_cols):
    dataFrame = pandass.DataFrame(np.ones((rows, len_all_cols)) * np.nan)
    for y, row in enumerate(len_all_rows):
        try:
            col1 = dataFrame.iloc[y, :][dataFrame.iloc[y, :].isnull()].index[0]
        except IndexError:
            print(i, row)

        for j, csv in enumerate(row.find_all(['td', 'th'])):
            row, col = get_row_col(csv)

            while any(dataFrame.iloc[y, col1:col1 + col].notnull()):
                col1 += 1

            dataFrame.iloc[y:y + row, col1:col1 + col] = csv.getText()
            if col1 < dataFrame.shape[1] - 1:
                col1 += col

    return dataFrame


URL = "https://en.wikipedia.org/wiki/2019_in_spaceflight#Orbital_launches"
res = requests.get(URL).text
soup = BeautifulSoup(res, "html.parser")
tables = soup.findAll("table", class_='wikitable')
table = tables[0]

len_all_rows, rows, len_all_cols = process(table)
df = process_all(len_all_rows, rows, len_all_cols)

df1 = df.transpose()
l0 = df[0] #date
l1 = df[6] #value

for i in range(len(l0)):
    w = l0[i]
    head, sep, tail = w.partition('[')
    l0[i] = head
    if l0[i].count(':') == 1:
        l0[i] = l0[i] + ":00"
    l0[i] = l0[i][:-8] + " 2019 " + l0[i][-8:]

word = ["Operational", "En route", "Successful"]
extractedData = {}
cnt = 100
for i in range(len(l0)):
    if isinstance(l1[i], str):
        if l1[i].count(word[0]) or l1[i].count(word[1]) or l1[i].count(word[2]):
            extractedData[l0[i] + str(cnt)] = l1[i]
            cnt += 1

extractedDataCount = defaultdict(int)
for key, value in extractedData.items():
    if key[:-3] not in extractedDataCount:
        extractedDataCount[key[:-3]] = 1
    else:
        extractedDataCount[key[:-3]] += 1

extractedDataFiltered = defaultdict(int)
for key, value in extractedDataCount.items():
    temp = ' '.join(key.split(' ')[0:2])
    extractedDataFiltered[temp] += 1

# for key, value in m2.items():
#     print(key, value)

finalDict = defaultdict(int)
for key, value in extractedDataFiltered.items():
    temp_key = key + " 2019 00:00:00"
    date = datetime.datetime.strptime(temp_key, '%d %B %Y %H:%M:%S')
    date.isoformat()
    finalDict[date] = value

ansval = []
ansdate = []

#formatting as per ISO 8601
for key, value in finalDict.items():
    ansval.append(value)
    temp_key = str(key).replace(' ', 'T')
    temp_key += "+00:00"
    ansdate.append(temp_key)
"""
for i in range(len(ansdate)):
    print(ansdate[i])
"""

#start and end date of 2019
start = datetime.datetime.strptime("01-01-2019", "%d-%m-%Y")
end = datetime.datetime.strptime("31-12-2019", "%d-%m-%Y")
date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days + 1)]

final = defaultdict(int)
for i in range(len(date_generated)):
    final[date_generated[i].isoformat() + "+00:00"] = 0

for i in range(len(ansdate)):
    if ansdate[i] in final:
        final[ansdate[i]] = ansval[i]

# for key, value in final.items():
#     print(key, value)

#Putting in CSV
with open('result.csv', 'w') as f:
    f.write("date, value\n")
    for key in final.keys():
        f.write("%s,%s\n" % (key, final[key]))
