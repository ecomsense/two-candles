from constants import logging, O_FUTL
from requests import get
import pandas as pd
import json

diff = {"BANKNIFTY": 100, "NIFTY": 50}


class Symbol:
    def __init__(self, dump):
        self.dump = dump
        if O_FUTL.is_file_not_2day(dump):
            url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            headers = {
                "Host": "angelbroking.com",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            resp = get(url, headers=headers)
            if resp.status_code == 200:
                with open(dump, "w") as json_file:
                    json_file.write(resp.text)

    def get_tokens(self, lst):
        """
        input:
            lst: list of exchange and symbol seperated by ':'
        output:
            dct: dictionary of exchange,symbol and token
        """
        dct = {}
        with open(self.dump, "r") as objfile:
            data = json.load(objfile)
            df = pd.DataFrame(data)
        print(df.columns)

        for i in lst:
            lst_excsym = i.split(":")
            exch = lst_excsym[0]
            sym = lst_excsym[1] + "-EQ"
            try:
                dct[i] = df.loc[(df["exch_seg"] == exch) & (df["symbol"] == sym)][
                    "token"
                ].values[0]
            except Exception as e:
                logging.warning(f"{__name__}: {sym} {e}")

        return dct
