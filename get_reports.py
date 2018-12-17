import pickle

import html2text
import lxml.html
import pandas as pd
import requests

df = pd.read_csv('sp-500.csv', sep=',', header=0)
site = 'https://www.sec.gov'
link = lambda cik: 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={}&type=def+14A&dateb=&owner=exclude&count=40'.format(cik)
ciks = df['Symbol']
names = list(df['Name'])

reports =[]
f = open('companies.pkl', 'ab+')
l = open('loading_report.txt', 'a+')
for i, cik in enumerate(list(ciks)):
    response = requests.get(link(cik))
    tree = lxml.html.fromstring(response.text)

    urls = tree.xpath('//a/@href')
    url_names = tree.xpath("//a[text()=' Documents']/@href")

    try:
        report_site_url = url_names[0]
    except:
        report = ""
        pickle.dump(report, f)
        err = '{} report not found'.format(names[i])
        print(err)
        l.write(err)
        continue

    report_response = requests.get(site + report_site_url)
    report_tree = lxml.html.fromstring(report_response.text)

    url_names = report_tree.xpath("//a[contains(text(), 'htm')]/@href")

    try:
        report = requests.get(site + url_names[0])
    except:
        report = ""
        pickle.dump(report, f)
        err = '{} htm file not found'.format(names[i])
        print(err)
        l.write(err)
        continue

    h = html2text.HTML2Text()
    h.ignore_links = True
    report = h.handle(report.text)
    # reports.append(report)
    pickle.dump(report, f)
    res = '{} report successfully added'.format(names[i])
    print(res)
    l.write(res)
    continue

f.close()
l.close()