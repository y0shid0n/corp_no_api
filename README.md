# corp_no_api
corporate number search api

https://www.houjin-bangou.nta.go.jp/webapi/

## Usage

1. registrate to API

  1. you can registrate from from the above URL and get API key.

1. create config.yml

  1. copy `conf/config.yml.template` to `conf/config.yml`.

  1. update `api_key` to your API key. (if necessary, update other params.)

1. execute API

  1. you can check all arguments by following command.

    ```python
    python download_data.py -h
    # usage: download_data.py [-h] (-c CORPNO | -d DATE | -p PERIOD PERIOD | -n NAME)
    #                         [--type {01,02,12}] [--divide DIVIDE] [--history {0,1}]
    #                         [--address ADDRESS]
    #                         [--kind [{01,02,03,04} [{01,02,03,04} ...]]]
    #                         [--fromto FROMTO FROMTO] [--mode {1,2}]
    #                         [--target {1,2,3}] [--change {0,1}] [--close {0,1}]
    ```

## Requirements

python(>=3.6) and the following libraries:

* requests
* pyyaml
