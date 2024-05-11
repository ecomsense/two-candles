import pendulum as pdlm
from constants import logging
from traceback import print_exc
import pandas as pd


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
        pd.DataFrame(lst).to_csv(f_fast, index=False)
        return symtkn

    def fast(self, symtkn):
        try:
            f_fast = self.data + symtkn["symbol"] + "/" + "fast.csv"
            if symtkn.get("last_update", None) and (
                pdlm.now() - symtkn["last_update"] < pdlm.duration(minutes=15)
            ):
                symtkn["fast"] = pd.read_csv(f_fast)
            else:
                symtkn = self._get_history(symtkn, f_fast)
                symtkn["last_update"] = pdlm.now()
            return symtkn
        except Exception as e:
            print(e)
            print_exc()

    def slow(self, symtkn):
        pass

    def on_tick(self, lst_of_exchsym):
        resp = self.api.ltp(lst_of_exchsym)
        print(resp)
        pass

    def signal(self):
        pass
