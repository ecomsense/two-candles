from constants import logging, O_FUTL, S_DATA
import pandas as pd
from toolkit.kokoo import timer
from traceback import print_exc


def find_indices(df, minv, maxv):
    long = len(df)
    logging.debug(f"length {long=} vs subset {maxv}")
    minimum_candles = 6

    if long >= minimum_candles:
        start = long - min(maxv, long) - 3
        end = long
    else:
        return None

    # initilize tuple and append start and end
    lst = []

    def find_start_and_end(df, start, end):
        try:
            logging.debug(f"filtering from {start=} {end=}")
            # print(df[start : end + 1])
            sdf = df[start : end - 3 - minv]
            candle_b = end - 3
            candle_a = sdf["high"].idxmax()
            lst.append((candle_a, candle_b))
            # print the value of df.index 122
            high_b = df.loc[candle_b, "high"]
            high_a = df.loc[candle_a, "high"]
            logging.debug(f"{candle_a=} {high_a=}")
            logging.debug(f"{candle_b=} {high_b=}")
            start = candle_a - maxv - 3
            end = candle_a + 3
            print(sdf)
            if start < 0 and end >= 6:
                start = 0
            logging.debug(f"coming up next {start=}{end=}")
            return start, end
        except Exception as e:
            print(e)
            print_exc()

    while end > 6:
        start, end = find_start_and_end(df, start, end)
        timer(2)
    else:
        return lst


def eval_variance(lst, df, var):
    try:
        logging.debug("variace")
        evaluated = []

        def variance(tpl):
            candle_a, candle_b = tpl
            logging.debug(f"{candle_a=} {candle_b=}")
            a_high = df.iloc[candle_a]["high"]
            b_high = df.iloc[candle_b]["high"]
            logging.debug(f"{a_high=} {b_high=}")
            var_perc = float((a_high - b_high) / a_high * 100)
            logging.debug(f"{var} > {abs(var_perc)}")
            return var > abs(var_perc)

        for i in lst:
            logging.debug(str(i))
            flag = variance(i)
            if flag:
                evaluated.append(i)
    except Exception as e:
        print(e)
        print_exc()
    finally:
        return evaluated


def eval_higher_low(lst, df):
    try:
        logging.debug("evaluating higher low")
        hl = []

        def higher_low(tpl):
            truths = []
            for _, v in enumerate(tpl):
                elder = v + 1
                younger = v + 2
                e_low = df.iloc[elder]["low"]
                y_low = df.iloc[younger]["low"]
                e_high = df.iloc[elder]["high"]
                y_high = df.iloc[younger]["high"]
                flag = y_low < e_low and y_high < e_high
                logging.debug(f"hh and hl {flag}")
                truths.append(flag)
            if all(truths):
                return True
            else:
                return False

        for i in lst:
            logging.debug(str(i))
            is_hl = higher_low(i)
            logging.debug(f"{is_hl=}")
            if is_hl:
                hl.append(i)
    except Exception as e:
        print(e)
        print_exc()
    finally:
        return hl


try:
    csv = S_DATA + "NSE:HINDALCO/fast.csv"
    df = pd.read_csv(csv)
    lst = find_indices(df, 10, 100)
    if len(lst) > 0:
        lst_var = eval_variance(lst, df, 0.1)
    if "lst_var" in locals() and len(lst_var) > 0:
        lst_hl = eval_higher_low(lst_var, df)
    if "lst_hl" in locals() and len(lst_hl) > 0:
        print(lst_hl)
except KeyboardInterrupt as e:
    print(e)
    __import__("sys").exit(1)
except Exception as e:
    print(e)
    print_exc()
