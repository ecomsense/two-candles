import pandas as pd


class Universe:
    def csv_to_list(self, S_UNIV):
        lst = []
        df = pd.read_csv(S_UNIV).dropna(axis=0).drop(["enable"], axis=1)
        for _, row in df.iterrows():
            # remove left and right spaces from string
            symbol = row["symbol"].strip(" ").upper()
            exchange = row["exchange"].strip(" ").upper()
            lst.append(exchange + ":" + symbol)
        return lst

    def dict_to_csv(self, lst_symtkns, S_OUT):
        df = pd.DataFrame(lst_symtkns)
        df.to_csv(S_OUT, index=False)
