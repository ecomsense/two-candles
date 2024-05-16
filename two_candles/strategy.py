from constants import logging, O_FUTL
from toolkit.kokoo import timer
from traceback import print_exc
import pandas as pd
import pendulum as pdlm
from typing import Tuple


class Strategy:
    def __init__(self, api, data, lst):
        self.api = api
        self.data = data
        self.lst = lst
        self.fm = (
            pdlm.now()
            .subtract(days=7)
            .set(hour=9, minute=15, second=0)
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        for symtkn in self.lst:
            if not O_FUTL.is_file_exists(
                self.data + symtkn["symbol"] + "/" + "fast.csv"
            ):
                print("creating directory and file")

    def _get_history(self, symtkn, f_fast):
        kwargs = {
            "instrument_token": symtkn["token"],
            "from_date": self.fm,
            "to_date": pdlm.now().strftime("%Y-%m-%d %H:%M:%S"),
            "interval": "15minute",
        }
        lst = self.api.kite.historical_data(**kwargs)
        lst = [
            dict(
                date=pdlm.instance(x["date"]).to_datetime_string(),
                open=x["open"],
                high=x["high"],
                low=x["low"],
                close=x["close"],
            )
            for x in lst
        ]
        symtkn["fast"] = lst
        # keep last 100 candles only

        self.df = pd.DataFrame(lst)[-100:]
        self.df.to_csv(f_fast, index=False)

    def fast(self, symtkn):
        try:
            f_fast = self.data + symtkn["symbol"] + "/" + "fast.csv"
            if symtkn.get("last_update", None) and (
                pdlm.now() - symtkn["last_update"] <= pdlm.duration(minutes=15)
            ):
                self.df = pd.read_csv(f_fast)
            else:
                self._get_history(symtkn, f_fast)
                symtkn["last_update"] = pdlm.now()
            return symtkn
        except Exception as e:
            print(e)
            print_exc()

    def on_tick(self, lst_of_exchsym):
        resp = self.api.ltp(lst_of_exchsym)
        print(resp)

    def find_highest_values(
        self,
        symtkn,
    ):
        self.indices = []
        self.fast(symtkn)
        sorted_df = self.df.sort_values(by="high", ascending=False)
        highest_indices = sorted_df.index[:2]

        if (
            abs(highest_indices[1] - highest_indices[0]) >= 10
            and abs(highest_indices[1] - highest_indices[0]) <= 100
            and len(self.df) > max(highest_indices) + 2
            and sorted_df.iloc[0]["high"] - sorted_df.iloc[1]["high"] < 10
        ):
            self.indices = highest_indices

    def eval_highs(self):
        try:
            hl = []

            def highs(tpl):
                truths = []
                for _, v in enumerate(tpl):
                    younger = v + 1
                    elder = v + 2
                    e_low = self.df.iloc[elder]["low"]
                    y_low = self.df.iloc[younger]["low"]
                    e_high = self.df.iloc[elder]["high"]
                    y_high = self.df.iloc[younger]["high"]
                    flag = y_low < e_low and y_high < e_high
                    logging.debug(f"is candle #{v} followed by hh and lh ? {flag}")
                    truths.append(flag)
                if all(truths):
                    candle_a, candle_b = tpl
                    logging.info(f"{candle_a=} {candle_b=}")
                    highest_candle = max(
                        self.df.iloc[candle_a]["high"], self.df.iloc[candle_b]["high"]
                    )
                    logging.debug(f"{highest_candle=}")
                    return highest_candle
                else:
                    return None

            if len(self.indices) > 0:
                logging.debug("evaluating ... highs")
                for i in self.indices:
                    logging.debug(str(i))
                    is_hl = highs(i)
                    logging.debug(f"{is_hl=}")
                    if is_hl:
                        hl.append(is_hl)
        except Exception as e:
            print(e)
            print_exc()
        finally:
            return hl

    def run(self):
        for symtkn in self.lst:
            logging.info(f"processing ... {symtkn['symbol']}")
            self.find_highest_values(symtkn)
            buy_triggers = self.eval_highs()
            print(buy_triggers)
