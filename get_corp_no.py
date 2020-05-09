# save csv from corporate number search api

import requests
from urllib.parse import urljoin
import io
import yaml
import csv
import time
import argparse
from datetime import datetime
from logging import getLogger, StreamHandler, Formatter
import hashlib

# create logger
logger = getLogger(__name__)
log_fmt = Formatter("%(asctime)s %(name)s %(lineno)s [%(levelname)s][%(funcName)s] %(message)s")

# set log level
log_level = "INFO"
logger.setLevel(log_level)

# create handler
handler = StreamHandler()
handler.setLevel(log_level)
handler.setFormatter(log_fmt)
logger.addHandler(handler)

def create_args():
    """
    create args
    """
    parser = argparse.ArgumentParser(description="download corporate number csv")
    g_main = parser.add_mutually_exclusive_group(required=True) # you must set either "-c", "-d", "-p" or "-n"
    g_main.add_argument("-c", "--corpno", type=int, help="target corporate number: 13-digit integer")
    g_main.add_argument("-d", "--date", type=str, help="target date: YYYY-MM-DD")
    g_main.add_argument("-p", "--period", action="store_true", help="whether to set target period")
    g_main.add_argument("-n", "--name", type=str, help="corporate name: hoge")
    g_sub = parser.add_argument_group("sub group")
    g_sub.add_argument("--start", type=str, help="start date (use with --period or --name): YYYY-MM-DD")
    g_sub.add_argument("--end", type=str, help="end date (use with --period or --name): YYYY-MM-DD")
    g_sub.add_argument("--type", type=str, choices=["01", "02", "12"], default="02", help="output file type: csv(sjis), csv(utf8) or xml")
    g_sub.add_argument("--divide", type=int, default=None, help="separated number") # to judge whether to repeat, default value is None
    g_opt = parser.add_argument_group("optional group")
    g_opt.add_argument("--history", type=int, choices=[0, 1], default=0, help="wheter to get old info (use with --corpno)")
    g_opt.add_argument("--address", type=int, help="area code (use with --date or --name): 2-digit or 5-digit integer")
    g_opt.add_argument("--kind", type=str, nargs="*", default=["01", "02", "03", "04"], choices=["01", "02", "03", "04"]
        , help="corporate type (use with --date or --name): government agency, local government, corpration or others")
    g_opt.add_argument("--mode", type=int, choices=[1, 2], default=1, help="search type (use with --name): prefix match or partial match")
    g_opt.add_argument("--target", type=int, choices=[1, 2, 3], default=1, help="search target (use with --name): fuzzy search, exact match or English")
    g_opt.add_argument("--change", type=int, choices=[0, 1], default=0, help="wheter search old info (use with --name)")
    g_opt.add_argument("--close", type=int, choices=[0, 1], default=1, help="wheter search closed corporation (use with --name)")
    args = parser.parse_args()

    return args

def create_payload(api_key, **kwargs):
    """
    create url and payload depending on args
    """
    # default payload
    payload = {
        "id": api_key,
        "type": kwargs["type"]
    }

    if kwargs["corpno"]:
        payload["number"] = kwargs["corpno"]
        payload["history"] = kwargs["history"]
    elif kwargs["date"]:
        payload["from"] = kwargs["date"]
        payload["to"] = kwargs["date"]
        payload["kind"] = kwargs["kind"]
        payload["divide"] = kwargs["divide"]
        if kwargs["address"]:
            payload["address"] = kwargs["address"]
    elif kwargs["period"]:
        payload["from"] = kwargs["start"]
        payload["to"] = kwargs["end"]
        payload["kind"] = kwargs["kind"]
        payload["divide"] = kwargs["divide"]
        if kwargs["address"]:
            payload["address"] = kwargs["address"]
    else:
        payload["name"] = kwargs["name"]
        payload["mode"] = kwargs["mode"]
        payload["target"] = kwargs["target"]
        payload["kind"] = kwargs["kind"]
        payload["change"] = kwargs["change"]
        payload["close"] = kwargs["close"]
        payload["from"] = kwargs["start"]
        payload["to"] = kwargs["end"]
        payload["divide"] = kwargs["divide"]
        if kwargs["address"]:
            payload["address"] = kwargs["address"]

    return payload


def fetch_data(api_url, api_key, **kwargs):
    """
    fetch data using created url and payload
    """
    payload = create_payload(api_key, **kwargs)
    logger.debug(payload)

    if kwargs["corpno"]:
        api_url = urljoin(api_url, "num")
    elif kwargs["date"] or kwargs["period"]:
        api_url = urljoin(api_url, "diff")
    else:
        api_url = urljoin(api_url, "name")

    res = requests.get(api_url, params=payload)
    logger.debug(res.url)

    # ToDo: error check
    if res.status_code != 200:
        logger.error("*****http error!!!*****")
        logger.error(f"status code: {res.status_code}")
        exit(1)

    return res

def save_csv(res, columns, **kwargs):
    """
    save csv file from response
    """
    reader = csv.reader(io.StringIO(res.text))

    # get separate number from header
    line1 = next(reader) # drop header
    logger.debug(f"header info: {line1}")
    sep_cnt = line1[2]
    sep_num = line1[3]

    # create filename
    if kwargs["corpno"]:
        tmp = kwargs["corpno"]
    elif kwargs["date"]:
        tmp = kwargs["date"].replace("-", "")
    elif kwargs["period"]:
        tmp = kwargs["start"].replace("-", "") + "-" + kwargs["end"].replace("-", "")
    else:
        tmp = kwargs["name"]

    # create hash value of args
    hs = hashlib.md5(str(kwargs).encode()).hexdigest()
    filename = f"./output/result_{tmp}_{sep_cnt}_{hs}.csv"

    with open(filename, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(reader)

    return int(sep_num) # for repeat

if __name__ == "__main__":
    # create args
    args = create_args()
    logger.debug(args)

    # because it is need to judge repeat later, when args.divide is not set, it is need to be remained.
    # however, because api expects default value is 1, args_dict["divide"] is only updated.
    args_dict = vars(args).copy()
    if not args.divide:
        args_dict["divide"] = 1

    # check corporate number
    if args.corpno and len(str(args.corpno)) != 13:
        logger.error("*****corporate number must be 13-digit integer*****")
        exit(1)

    # check date
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            logger.error("*****date must be defined by YYYY-MM-DD*****")
            exit(1)
    if args.start or args.end:
        try:
            datetime.strptime(args.start, "%Y-%m-%d")
            datetime.strptime(args.end, "%Y-%m-%d")
        except (ValueError, TypeError):
            logger.error("*****both start and end must be defined by YYYY-MM-DD*****")
            exit(1)

    # read yaml
    with open("./conf/config.yml") as f:
        conf = yaml.safe_load(f)

    # get api info from yaml
    api_url = conf["default"]["api_url"]
    api_key = conf["default"]["api_key"]

    # define columns of csv
    columns = [
        "sequenceNumber", "corporateNumber", "process", "correct", "updateDate"
        , "changeDate", "name", "nameImageId", "kind", "prefectureName"
        , "cityName", "streetNumber", "addressImageId", "prefectureCode", "cityCode"
        , "postCode", "addressOutside", "addressOutsideImageId", "closeDate", "closeCause"
        , "successorCorporateNumber", "changeCause", "assignmentDate", "latest", "enName"
        , "enPrefectureName", "enCityName", "enAddressOutsid", "furigana", "hihyoji"
    ]

    # download csv
    res = fetch_data(api_url, api_key, **args_dict)
    sep_num = save_csv(res, columns, **args_dict)

    # repeat until all separated data are downloaded
    # when args.divide is not set, fetch_data is not repeated
    if not args.divide and sep_num > 1:
        for i in range(2, sep_num + 1):
            time.sleep(5)
            args_dict["divide"] = i
            res = fetch_data(api_url, api_key, **args_dict)
            sep_num = save_csv(res, columns, **args_dict)
