from constants import logging, O_FUTL, S_JSON
from toolkit.kokoo import timer
from traceback import print_exc
import pandas as pd
import pendulum as pdlm
from pprint import pprint


class Strategy:
    def __init__(self, api, data, lst):
        self.api = api
        self.data = data
        self.signals_file = data + "signals.csv"
        columns = [
            "signal",
            "symbol",
            "candle_a",
            "extreme_a",
            "candle_b",
            "extreme_b",
            "trigger",
            "sl",
        ]
        pd.DataFrame(columns=columns).to_csv(self.signals_file, index=False)

        temp = O_FUTL.read_file(S_JSON)
        if temp:
            list_of_symbols = [y["symbol"] for y in temp]
            # build append items to the temp
            for x in lst:
                if x["symbol"] not in list_of_symbols:
                    logging.info(f"strategy found {x['symbol']} ")
                    temp.append(x)
            self.lst = temp
        else:
            self.lst = lst
        O_FUTL.write_file(S_JSON, self.lst)
        self.fm = (
            pdlm.now()
            .subtract(days=7)
            .set(hour=9, minute=15, second=0)
            .strftime("%Y-%m-%d %H:%M")
        )
        print(self.fm)
        for symtkn in self.lst:
            filepath = self.data + symtkn["symbol"] + "/" + "fast.csv"
            if not O_FUTL.is_file_exists(filepath):
                print("creating {filepath=}")

    def _get_history(self, symtkn, f_fast):
        try:
            logging.debug(f"getting history for {symtkn['symbol']}")
            kwargs = {
                "exchange": "NSE",
                "symboltoken": symtkn["token"],
                "fromdate": str(self.fm),
                "todate": str(pdlm.now().strftime("%Y-%m-%d %H:%M")),
                "interval": "FIFTEEN_MINUTE",
            }
            lst = self.api.obj.getCandleData(kwargs)["data"]
            lst = [
                dict(
                    date=x[0],
                    open=x[1],
                    high=x[2],
                    low=x[3],
                    close=x[4],
                )
                for x in lst
            ]
            # keep last 100 candles only
            df = pd.DataFrame(lst[-104:])
            df.to_csv(f_fast, index=False)
        except Exception as e:
            print(e)
            print_exc()

    def fast(self, symtkn):
        try:
            f_fast = self.data + symtkn["symbol"] + "/" + "fast.csv"
            mtime = O_FUTL.get_file_mtime(f_fast)
            # convert to gmt +5
            last_update = pdlm.from_format(
                mtime, "YYYY-MM-DD HH:mm:ss", tz="Asia/Kolkata"
            )
            logging.debug(f"last update time {last_update}")
            if pdlm.now() - last_update >= pdlm.duration(minutes=1):
                self._get_history(symtkn, f_fast)
            self.df = pd.read_csv(f_fast)
        except Exception as e:
            print(f"fast {e}")
            print_exc()

    def find_highest_values(
        self,
        symtkn,
    ):
        self.indices = []
        self.fast(symtkn)
        sorted_df = self.df.sort_values(by="high", ascending=False)
        highest_indices = sorted_df.index[:2].sort_values()
        highest_1 = self.df.iloc[highest_indices[0]]["high"]
        highest_2 = self.df.iloc[highest_indices[1]]["high"]
        date_1 = self.df.iloc[highest_indices[0]]["date"]
        date_2 = self.df.iloc[highest_indices[1]]["date"]
        if (
            highest_indices[1] - highest_indices[0] >= 10
            and highest_indices[1] - highest_indices[0] <= 100
            and len(self.df) > highest_indices[1] + 2
            and highest_indices[0] - 2 > 0
            and abs(highest_1 - highest_2) / max(highest_1, highest_2) * 100 < 10
        ):
            self.indices = highest_indices
            logging.info(f"MATCH FOUND: {highest_1}@{date_1} {highest_2}@{date_2}")

    def eval_highs(self, symbol) -> int:
        try:
            highest = 0

            def highs(candle_a, candle_b, sl):
                a_date = self.df.iloc[candle_a]["date"]
                ay = candle_a - 1
                ay_high = self.df.iloc[ay]["high"]
                ae = candle_a - 2
                ae_high = self.df.iloc[ae]["high"]

                b_date = self.df.iloc[candle_b]["date"]
                by = candle_b + 1
                by_high = self.df.iloc[by]["high"]
                be = candle_b + 2
                be_high = self.df.iloc[be]["high"]

                a_flag = ay_high > ae_high
                b_flag = by_high > be_high
                txt = f"is candle #{candle_a} {a_date} preceded by LHs ? {ay_high}>{ae_high} {a_flag}"
                logging.info(txt)
                txt = f"is candle #{candle_b} {b_date} followed by LHs ? {by_high}>{be_high} {b_flag}"
                logging.info(txt)
                if a_flag and b_flag:
                    highest_candle = max(
                        self.df.iloc[candle_a]["high"], self.df.iloc[candle_b]["high"]
                    )
                    logging.debug(f"{highest_candle=}")
                    self.signal = dict(
                        signal="long",
                        symbol=symbol,
                        candle_a=self.df.iloc[candle_a]["date"],
                        extreme_a=self.df.iloc[candle_a]["high"],
                        candle_b=self.df.iloc[candle_b]["date"],
                        extreme_b=self.df.iloc[candle_b]["high"],
                        trigger=highest_candle,
                        sl=sl,
                    )
                    return highest_candle
                else:
                    return 0

            if len(self.indices) > 0:
                candle_a, candle_b = self.indices[0], self.indices[1]
                df = self.df.iloc[candle_a - 2 :]
                lowest = df["low"].min()
                subset_df = self.df.iloc[candle_a:candle_b]
                cup_low = subset_df["low"].min()
                logging.info(f"{cup_low=}  is equal to {lowest=} ?")
                if cup_low == lowest:
                    highest = highs(candle_a, candle_b, lowest)

        except Exception as e:
            print(e)
            print_exc()
        finally:
            return highest

    def run(self):
        df = pd.read_csv(self.signals_file)
        while True:
            for symtkn in self.lst:
                logging.info(f"processing ... {symtkn['symbol']}")
                is_position = symtkn.get("is_position", -11)
                if is_position == -11 or is_position == 0:
                    symtkn["is_position"] = 0
                    self.find_highest_values(symtkn)
                    highest = self.eval_highs(symtkn["symbol"])
                    if highest > 0:
                        symtkn["is_position"] = 1
                        new_row = pd.DataFrame(self.signal, index=[df.shape[0]])
                        df = pd.concat([df, new_row], ignore_index=True)
                        df.to_csv(self.signals_file, index=False)
                        print(50 * "-")
                timer(1)
            pprint(self.lst)
            timer(3)
            O_FUTL.write_file(S_JSON, self.lst)
