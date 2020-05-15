# download csv from corporate number search api

import yaml
import time
from logging import getLogger, StreamHandler, Formatter, config
import xml.etree.ElementTree as ET
from xml.dom import minidom

# create logger
config.fileConfig('./conf/logging.conf')
logger = getLogger(__name__)

from corp_no_api import CorpNoApi


def xml2csv(xml_str, type, columns, filename, encoding="utf-8"):
    """
    convert xml to csv
    """
    # get separate number from header
    # there is header info from index 0 to index 3
    root = ET.fromstring(xml_str)
    logger.debug(f"header info: {root[0].text}, {root[1].text}, {root[2].text}, {root[3].text}")

    # there is corporation data in after index 4
    data_list = []
    for i in range(4, len(root) + 1):
        data_corp = [i for i in root[i].text]
        data_list.append(data_corp)

    with open(filename, "w", newline="", encoding=encoding) as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(data_list)


if __name__ == "__main__":
    # read yaml
    with open("./conf/config.yml") as f:
        conf = yaml.safe_load(f)

    # get api info from yaml
    api_url = conf["default"]["api_url"]
    api_key = conf["default"]["api_key"]

    # create output directory
    output_dir = "./output/"

    # create instance
    corp_no_api = CorpNoApi(api_url, api_key)

    # exec api and save file
    corp_no_api.download_data(output_dir)
