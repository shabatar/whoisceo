# Who Is CEO?

A flask webUI demo app to determine the CEO of a company by its CIK (Central Index Key).
Full list of companies has been taken from [S&P 500 Index](https://www.barchart.com/stocks/indices/sp/sp500?page=all)

## Before running

Before running the app, one needs to run

```
$ python3 get_reports.py
```

in order to load latest companies reports (DEF 14 A) from [US Exchange Commission website](https://www.sec.gov/edgar/searchedgar/companysearch.html).


As soon as the reports are pickled, run

```
$ python3 search.py
```

in order to perform search in reports.

### Deploy and Run app in Docker

```
$ docker build -t whoisceo:latest . 
```

```
$ docker run -d -p 5000:5000 whoisceo
```

Then go to 127.0.0.1:5000 inside a browser of any kind.
