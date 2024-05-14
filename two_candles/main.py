from constants import logging, O_CNFG, O_SETG, S_DATA, S_UNIV, S_OUT, S_DUMP
from login import get_bypass
from symbol import Symbol
from universe import Universe
from strategy import Strategy
from toolkit.kokoo import is_time_past, dt_to_str, blink
from traceback import print_exc
import pandas as pd

T_START = "9:45"
T_STOP = "3:28"


def init():
    try:
        Sym = Symbol(S_DUMP)
        Unv = Universe()
        lst = Unv.csv_to_list(S_UNIV)
        logging.info(f"qualified {lst}")
        dct = Sym.get_tokens(lst)
        lst = [{"symbol": k, "token": v} for k, v in dct.items()]
        logging.info(f" tokens {lst}")
        Unv.dict_to_csv(lst, S_OUT)
    except Exception as e:
        print(e)
        print_exc()
        __import__("sys").exit(1)
    return lst


def main():
    lst = init()
    try:
        Api = get_bypass(O_CNFG, S_DATA)
    except Exception as e:
        logging.error(e)
        print_exc()

    Strategy(Api, S_DATA, lst).run()


main()
