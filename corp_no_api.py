# define call web api class

import io
import csv
import yaml
import time
import hashlib
import requests
import argparse
from datetime import date
from logging import getLogger
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from xml.dom import minidom

# create logger
logger = getLogger(__name__)

class CorpNoApi:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.args = None
        self.divide = 1
        self.columns = [
            "sequenceNumber", "corporateNumber", "process", "correct", "updateDate"
            , "changeDate", "name", "nameImageId", "kind", "prefectureName"
            , "cityName", "streetNumber", "addressImageId", "prefectureCode"
            , "cityCode", "postCode", "addressOutside", "addressOutsideImageId"
            , "closeDate", "closeCause", "successorCorporateNumber", "changeCause"
            , "assignmentDate", "latest", "enName", "enPrefectureName"
            , "enCityName", "enAddressOutsid", "furigana", "hihyoji"
        ] # columns of csv (30 columns)

    def date_type(self, date_str):
        """
        type of args used for --date, --start and --end in create_args()
        it must be string formatted with YYYY-MM-DD
        """
        try:
            date.fromisoformat(date_str)
        except ValueError as e:
            raise argparse.ArgumentTypeError(str(e)
                + " date must be in ISO format(YYYY-MM-DD)")
        return date_str


    def create_args(self):
        """
        create args
        """
        parser = argparse.ArgumentParser(
            description="download corporate number and related information by csv"
            )
        g_main = parser.add_argument_group("main args")
        # you must set either "-c", "-d", "-p" or "-n"
        g_excl = g_main.add_mutually_exclusive_group(required=True)
        g_excl.add_argument("-c", "--corpno", type=int
            , help="target corporate number: 13-digit integer")
        g_excl.add_argument("-d", "--date", type=self.date_type
            , help="target date: YYYY-MM-DD")
        g_excl.add_argument("-p", "--period", type=self.date_type, nargs=2
            , help="start and end date: YYYY-MM-DD")
        g_excl.add_argument("-n", "--name", type=str, help="corporate name: hoge")

        g_sub = parser.add_argument_group("sub args")
        g_sub.add_argument("--type", type=str, choices=["01", "02", "12"]
            , default="02"
            , help="output file type: csv(sjis), csv(utf8) or xml")
        # to judge whether to repeat, default value of --divide is None
        g_sub.add_argument("--divide", type=int, default=None
            , help="target separated number")

        g_opt = parser.add_argument_group("additional args")
        g_opt.add_argument("--history", type=int, choices=[0, 1], default=0
            , help="wheter to get old info (use with --corpno)")
        g_opt.add_argument("--address", type=int
            , help="area code (use with --date, --period or --name): \
                2-digit or 5-digit integer")
        g_opt.add_argument("--kind", type=str, nargs="*"
            , default=["01", "02", "03", "04"], choices=["01", "02", "03", "04"]
            , help="corporate type (use with --date, --period or --name): \
                government agency, local government, corpration or others")
        g_opt.add_argument("--fromto", type=self.date_type, nargs=2
            , help="start and end date (use with --name): YYYY-MM-DD")
        g_opt.add_argument("--mode", type=int, choices=[1, 2], default=1
            , help="search type (use with --name): prefix match or partial match")
        g_opt.add_argument("--target", type=int, choices=[1, 2, 3], default=1
            , help="search target (use with --name): \
                fuzzy search, exact match or English")
        g_opt.add_argument("--change", type=int, choices=[0, 1], default=0
            , help="whether search old information (use with --name)")
        g_opt.add_argument("--close", type=int, choices=[0, 1], default=1
            , help="whether search closed corporation (use with --name)")
        self.args = parser.parse_args()

        if self.args.divide:
            self.divide = self.args.divide

        return self.args


    def create_payload(self):
        """
        create url and payload depending on args
        """
        # default payload
        payload = {
            "id": self.api_key,
            "type": self.args.type
        }

        if self.args.corpno:
            payload["number"] = self.args.corpno
            payload["history"] = self.args.history
        elif self.args.date:
            payload["from"] = self.args.date
            payload["to"] = self.args.date
            payload["kind"] = self.args.kind
            payload["divide"] = self.divide
            if self.args.address:
                payload["address"] = self.args.address
        elif self.args.period:
            payload["from"] = self.args.period[0]
            payload["to"] = self.args.period[1]
            payload["kind"] = self.args.kind
            payload["divide"] = self.divide
            if self.args.address:
                payload["address"] = self.args.address
        else:
            payload["name"] = self.args.name
            payload["mode"] = self.args.mode
            payload["target"] = self.args.target
            payload["kind"] = self.args.kind
            payload["change"] = self.args.change
            payload["close"] = self.args.close
            payload["divide"] = self.divide
            if self.args.fromto:
                payload["from"] = self.args.fromto[0]
                payload["to"] = self.args.fromto[1]
            if self.args.address:
                payload["address"] = self.args.address

        return payload


    def fetch_data(self, payload):
        """
        fetch data using created url and payload
        """
        if self.args.corpno:
            url = urljoin(self.api_url, "num")
        elif self.args.date or self.args.period:
            url = urljoin(self.api_url, "diff")
        else:
            url = urljoin(self.api_url, "name")

        res = requests.get(url, params=payload)
        logger.debug(res.url)

        # ToDo: error check
        if res.status_code != 200:
            logger.error(f"***http error!!!***; status code: {res.status_code}; response: {res.text}")
            exit(1)

        return res


    def create_filename(self, divide):
        """
        create file name from args
        """
        # create filename
        if self.args.corpno:
            tmp = self.args.corpno
        elif self.args.date:
            tmp = self.args.date.replace("-", "")
        elif self.args.period:
            tmp = self.args.period[0].replace("-", "") + "-" \
                + self.args.period[1].replace("-", "")
        else:
            tmp = self.args.name

        # create hash value of args
        hs = hashlib.md5(str(self.args).encode()).hexdigest()

        # create extension
        if self.args.type == "12":
            ext = "xml"
        elif self.args.type in ["01", "02"]:
            ext = "csv"
        else:
            logger.error(f'invalid encoding type: {type}. it must be set "01", "02" or "12".')
            exit(1)

        self.filename = f"result_{tmp}_{divide}_{hs}.{ext}"

        return self.filename


    def define_encoding(self):
        """
        define file encoding to save
        """
        # define encoding
        if self.args.type == "01":
            self.encoding = "cp932"
        elif self.args.type in ["02", "12"]:
            self.encoding = "utf-8"
        else:
            logger.error(f'invalid encoding type: {type}. it must be set "01", "02" or "12".')
            exit(1)

        return self.encoding


    def save_csv(self, res, output_dir="./output/"):
        """
        save csv file from response
        """
        reader = csv.reader(io.StringIO(res.text))

        # get separate number from header
        line1 = next(reader) # drop header
        logger.debug(f"header info: {line1}")
        sep_cnt = line1[2]
        sep_num = line1[3]

        with open(output_dir + self.filename, "w", newline="", encoding=self.encoding) as f:
            writer = csv.writer(f)
            writer.writerow(self.columns)
            writer.writerows(reader)

        return int(sep_num) # for repeat


    def save_xml(self, res, output_dir="./output/"):
        """
        save xml file from response
        """
        root = ET.fromstring(res.text)
        logger.debug(f"header info: {root[0].text}, {root[1].text}, {root[2].text}, {root[3].text}")
        sep_cnt = root[2].text
        sep_num = root[3].text

        # parse xml formatted text
        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

        with open(output_dir + self.filename, "w", encoding=self.encoding) as f:
            f.write(xmlstr)

        return int(sep_num) # for repeat


    def download_data(self, output_dir="./output/"):
        """
        main function
        """
        # create args
        self.create_args()
        logger.debug(f"all args: {self.args}")

        # check corporate number
        if self.args.corpno and len(str(self.args.corpno)) != 13:
            logger.error("*****corporate number must be 13-digit integer*****")
            exit(1)

        payload = self.create_payload()
        logger.debug(f"payload: {payload}")
        res = self.fetch_data(payload)
        filename = self.create_filename(self.divide)
        encoding = self.define_encoding()
        if self.args.type in ["01", "02"]:
            sep_num = self.save_csv(res, output_dir)
        else:
            sep_num = self.save_xml(res, output_dir)

        # repeat until all separated data are downloaded
        # when args.divide is not set, download is not repeated
        if not self.args.divide and sep_num > 1:
            for i in range(2, sep_num + 1):
                time.sleep(5)
                payload["divide"] = i
                res = self.fetch_data(payload)
                filename = self.create_filename(i)
                if self.args.type in ["01", "02"]:
                    sep_num = self.save_csv(res, output_dir)
                else:
                    sep_num = self.save_xml(res, output_dir)
