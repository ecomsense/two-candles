from constants import O_FUTL, S_DATA
import pandas as pd
from toolkit.kokoo import timer
from traceback import print_exc


def find_pairs_continuous(df, subset_size=100, start_row=9):
    pairs_set = set()
    end_of_df = len(df) - 1
    print(f"{end_of_df=}")
    remaining_rows = min(subset_size, end_of_df)
    start = -3
    end = -93

    # Iterate through the DataFrame
    while remaining_rows > 0:
        # Select subset of rows starting from the specified start_row
        subset = df.iloc[start_row + min(subset_size, remaining_rows)]

        # Index of the last row in the subset
        last_index = subset.index[-1]

        # Index of the row where 'high' column has the maximum value within the subset
        highest_index = subset["high"].idxmax()

        print(f"{last_index=}{highest_index=}")

        # Add the pair of indices to the set
        pairs_set.add((last_index, highest_index))

        # Update the start_row for the next iteration
        start_row = highest_index

        print(f"{subset_size=}{remaining_rows=}")
        if remaining_rows < subset_size:
            break

        timer(5)

    # Convert the set to a list and return
    pairs = list(pairs_set)
    return pairs


def find_indices(df, maxv):
    minv = 10
    long = len(df)
    print(f"length {long=} vs subset {maxv}")
    minimum_candles = 6

    if long >= minimum_candles:
        start = long - min(maxv, long) - 3
        end = long
    else:
        return None

    def find_start_and_end(df, start, end):
        try:
            print(f"filtering from {start=} {end=}")
            # print(df[start : end + 1])
            sdf = df[start : end - 3 - minv]
            candle_b = end - 3
            candle_a = sdf["high"].idxmax()
            # print the value of df.index 122
            high_b = df.loc[candle_b, "high"]
            high_a = df.loc[candle_a, "high"]
            print(f"{candle_a=} {high_a=}")
            print(f"{candle_b=} {high_b=}")
            start = candle_a - maxv - 3
            end = candle_a + 3
            # print(f"{start=}{end=}")
            print(sdf)
            return start, end
        except Exception as e:
            print(e)
            print_exc()

    while start >= minimum_candles:
        start, end = find_start_and_end(df, start, end)
        timer(2)


try:
    csv = S_DATA + "NSE:HINDALCO/fast.csv"
    df = pd.read_csv(csv)
    pairs = find_indices(df, 100)
    print("Pairs of indices:", pairs)
except KeyboardInterrupt as e:
    print(e)
    __import__("sys").exit(1)
except Exception as e:
    print(e)
    __import__("sys").exit(1)
