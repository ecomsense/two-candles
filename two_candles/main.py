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


def identify_mother_candles(df):
    mother_candles = []

    for i in range(len(df) - 2, 0, -1):  # Loop through the DataFrame from right to left
        m_candle = df.iloc[i]  # Mother candle

        # Check if the rightmost mother candle has at least two candles to its right
        if len(df) - i > 2:
            # Check if this candle is higher than the previous mother candles
            if len(mother_candles) == 0 or m_candle["high"] > max(
                mc["high"] for mc in mother_candles
            ):
                mother_candles.append(m_candle)
                if len(mother_candles) == 2:
                    # Check if the candles are at least 10 candles apart but not exceeding 100 candles
                    if (
                        abs(mother_candles[0].name - mother_candles[1].name) >= 10
                        and abs(mother_candles[0].name - mother_candles[1].name) <= 100
                    ):
                        # Identify elder and younger candles for each mother candle
                        return get_subsets(df, mother_candles)
                    else:
                        mother_candles.pop(0)

    return None


def get_subsets(df, mc):
    subsets = []
    for i in range(2):
        idx = mc[i].name
        print(f"mother candle index {idx}")
        if i == 0:
            candle_a = df.loc[idx : idx + 2]  # Select subset around first mother candle
            subsets.append(candle_a)
        else:
            candle_b = df.loc[
                idx : idx + 2
            ]  # Select subset around second mother candle
            subsets.append(candle_b)
    return subsets


# Example usage:
# pairs = find_pairs_continuous(df)
# print("Pairs of indices:", pairs)


def run(lst):
    try:
        Api = get_bypass(O_CNFG, S_DATA)
    except Exception as e:
        logging.error(e)
        print_exc()

    Sgy = Strategy(Api, S_DATA, lst)
    while True:
        for symtkn in Sgy.lst:
            lst = Sgy.fast(symtkn)["fast"]
            print(symtkn["symbol"])
            df = pd.DataFrame(lst)
            # pattern = identify_mother_candles(df)
            # symtkn = {**pattern, **symtkn}
            pattern = find_pairs_continuous(df)
            print(pattern)
        break


lst = init()
run(lst)
