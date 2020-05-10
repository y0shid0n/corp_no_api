# corp_no_api
corporate number search api

https://www.houjin-bangou.nta.go.jp/webapi/

## Usage

```python
python download_data.py -h
# usage: get_corp_no.py [-h] (-c CORPNO | -d DATE | -p PERIOD PERIOD | -n NAME)
#                       [--type {01,02,12}] [--divide DIVIDE] [--history {0,1}]
#                       [--address ADDRESS]
#                       [--kind [{01,02,03,04} [{01,02,03,04} ...]]]
#                       [--fromto FROMTO FROMTO] [--mode {1,2}]
#                       [--target {1,2,3}] [--change {0,1}] [--close {0,1}]
```

## Requirements

the following libraries:

* requests
* pyyaml
