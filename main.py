import pandas as pd
from datetime import datetime as dt


def get_weekday(date_str):
    return dt.weekday(dt.strptime(date_str, "%Y-%m-%d"))


def write_to_df(df_result, atm_id, encash, day):
    df_result.loc[df_result["atm_id"] == atm_id, day] = encash


def calculate_remains(df_in, i, funding_rate, current_remains, date):
    funding_cost = (current_remains * funding_rate) / 365
    current_remains -= funding_cost
    current_remains += df_in[date][i]

    return current_remains


def calculate_encash(remains, atm_id, df_atm_info):
    amount_to_encash = 0

    if remains <= 500000:
        difference = 500001 - remains
        amount_to_encash = difference

        encash_cost = df_atm_info.loc[df_atm_info["atm_id"] == atm_id, "incasationcost"].values[0]
        amount_to_encash += encash_cost

    return amount_to_encash


def main():
    df_in = pd.read_csv("test_private.csv", sep=",")
    df_atm_info = pd.read_csv("atm_info.csv", sep=";")
    df_funding_rate = pd.read_csv("funding_rate.csv", sep=";")

    dates = ["2023-09-01", "2023-09-02", "2023-09-03", "2023-09-04", "2023-09-05", "2023-09-06", "2023-09-07"]

    df_res = df_in.copy()
    df_res = df_res[['atm_id'] + dates]

    for i, atm_row in df_in.iterrows():
        atm_id = atm_row["atm_id"]
        remains = atm_row["remains"]
        worktime = eval(df_atm_info.loc[df_atm_info["atm_id"] == atm_id, "worktime_split"].values[0])
        encash_cost = df_atm_info.loc[df_atm_info["atm_id"] == atm_id, "incasationcost"].values[0]

        current_remains = remains

        for j in range(len(dates)):
            date = dates[j]
            date_weekday = get_weekday(date)

            is_date_active = bool(worktime[date_weekday])
            if not is_date_active:
                write_to_df(df_res, atm_id, 0, date)
                continue

            funding_rate = df_funding_rate.loc[df_funding_rate["value_day"] == date, "funding_rate"].values[0]

            before_remains = current_remains
            current_remains = calculate_remains(df_in, i, funding_rate, current_remains, date)

            amount_to_encash = calculate_encash(current_remains, atm_id, df_atm_info)

            if j != len(dates) - 1:
                n = j + 1
                while n < len(dates):
                    next_date = dates[n]
                    next_weekday = get_weekday(next_date)

                    is_next_active = bool(worktime[next_weekday])

                    next_funding_rate = df_funding_rate.loc[df_funding_rate["value_day"] == next_date, "funding_rate"].values[0]

                    if is_next_active:
                        break

                    current_remains = calculate_remains(df_in, i, next_funding_rate, current_remains, next_date)
                    amount_to_encash += calculate_encash(current_remains, atm_id, df_atm_info)

                    n += 1

            current_remains += amount_to_encash
            amount_to_encash += before_remains if amount_to_encash != 0 else 0
            write_to_df(df_res, atm_id, amount_to_encash, date)

    df_res.to_csv("data_private.csv", index=None)


if __name__ == '__main__':
    main()
