from constants import logging, O_FUTL
from toolkit.kokoo import timer
from traceback import print_exc
import pandas as pd
import pendulum as pdlm


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
        self.df = pd.DataFrame(lst)
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

    def find_indices(self, symtkn, minv, maxv):
        self.fast(symtkn)
        # initilize tuple and append start and end
        self.indices = []
        long = len(self.df)
        logging.debug(f"length {long=} vs subset {maxv}")
        minimum_candles = 6

        if long >= minimum_candles:
            start = long - min(maxv, long) - 3
            end = long
        else:
            return None

        def find_start_and_end(start, end):
            try:
                logging.debug(f"filtering from {start=} {end=}")
                # print(df[start : end + 1])
                sdf = self.df[start : end - 3 - minv]
                candle_b = end - 3
                candle_a = sdf["high"].idxmax()
                self.indices.append((candle_a, candle_b))
                # print the value of df.index 122
                high_b = self.df.loc[candle_b, "high"]
                high_a = self.df.loc[candle_a, "high"]
                logging.debug(f"{candle_a=} {high_a=}")
                logging.debug(f"{candle_b=} {high_b=}")
                start = candle_a - maxv - 3
                end = candle_a + 3
                # logging.debug(sdf)
                if start < 0 and end >= 6:
                    start = 0
                logging.debug(f"coming up next {start=}{end=}")
                return start, end
            except Exception as e:
                print(e)
                print_exc()

        while start > 0:
            start, end = find_start_and_end(start, end)
            timer(1)

    def eval_variance(self, var):
        try:
            self.variance = []

            def variance(tpl):
                candle_a, candle_b = tpl
                logging.debug(f"{candle_a=} {candle_b=}")
                a_high = self.df.iloc[candle_a]["high"]
                b_high = self.df.iloc[candle_b]["high"]
                logging.debug(f"{a_high=} {b_high=}")
                var_perc = float((a_high - b_high) / a_high * 100)
                logging.debug(f"{var} > {abs(var_perc)}")
                return var > abs(var_perc)

            if len(self.indices) > 0:
                logging.info("variance")
                for i in self.indices:
                    logging.debug(str(i))
                    flag = variance(i)
                    if flag:
                        self.variance.append(i)
        except Exception as e:
            print(e)
            print_exc()

    def eval_higher_low(self):
        try:
            hl = []

            def higher_low(tpl):
                truths = []
                for _, v in enumerate(tpl):
                    elder = v + 1
                    younger = v + 2
                    e_low = self.df.iloc[elder]["low"]
                    y_low = self.df.iloc[younger]["low"]
                    e_high = self.df.iloc[elder]["high"]
                    y_high = self.df.iloc[younger]["high"]
                    flag = y_low < e_low and y_high < e_high
                    logging.debug(f"hh and hl {flag}")
                    truths.append(flag)
                if all(truths):
                    logging.info("evaluating to ..True")
                    candle_a, candle_b = tpl
                    return max(
                        self.df.iloc[candle_a]["high"], self.df.iloc[candle_b]["high"]
                    )
                else:
                    return None

            if len(self.variance) > 0:
                logging.debug("evaluating higher low")
                for i in self.variance:
                    logging.debug(str(i))
                    is_hl = higher_low(i)
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
            logging.info(f"processing {symtkn['symbol']}")
            self.find_indices(symtkn, 10, 100)
            self.eval_variance(1)
            self.eval_higher_low()
            if "lst_hl" in locals() and len(lst_hl) > 0:
                logging.info(f"buy signal received {lst_hl}")
