import pandas as pd
from datetime import datetime as dt
import itertools


def get_weekday(date_str):
    return dt.weekday(dt.strptime(date_str, "%Y-%m-%d"))


def total_cost(funding_spending, encash_cost, encash_list):
    cost = funding_spending

    for i, encash in enumerate(encash_list):
        if encash > 0:
            cost += encash_cost

    return cost


def get_worktime_permutations(dates, worktime):
    saved_indexes = [i for i, x in enumerate(worktime) if x == 0]
    saved_indexes.append(get_weekday(dates[0]))

    patterns = []
    for i in range(len(worktime)):
        pattern = [1] * (i + 1) + [0] * (len(worktime) - i - 1)
        patterns.append(pattern)

    permutations = [list(i) for i in itertools.product([0, 1], repeat=len(worktime))]
    for i, _ in enumerate(permutations):
        for pos in saved_indexes:
            permutations[i][pos] = worktime[pos]

    return permutations


def write_to_df(df_result, atm_id, encash_list, dates):
    for i, encash in enumerate(encash_list):
        df_result.loc[df_result["atm_id"] == atm_id, dates[i]] = encash


def calculate_funding_cost(funding_rate, value):
    remains_after = value / (1 + (funding_rate / 365))
    return remains_after * funding_rate / 365


def calculate_encash(remains, before_remains):
    amount_to_encash = 0

    if remains <= 500000:
        difference = 500001 - remains
        amount_to_encash = difference + before_remains

    return amount_to_encash


def calculate_encash_result(remains, inputs, dates, permutation, funding_rates):
    result = []
    result_funding_spending = 0

    for i, date in enumerate(dates):
        remain_funding = []
        date_weekday = get_weekday(date)
        atm_input = inputs[i]

        is_date_active = bool(permutation[date_weekday])
        if not is_date_active:
            result.append(0)
            continue

        funding_rate = funding_rates[i]

        need_encash = calculate_encash(remains + atm_input, remains)
        remains += atm_input
        if need_encash != 0:
            remains = need_encash + atm_input

        remain_funding.append([remains, funding_rate])

        if i != len(dates) - 1:
            n = i + 1
            while n < len(dates):
                next_date = dates[n]
                next_weekday = get_weekday(next_date)
                next_atm_input = inputs[n]

                next_funding_rate = funding_rates[n]
                is_next_active = bool(permutation[next_weekday])

                if is_next_active:
                    break

                next_need_encash = calculate_encash(next_atm_input + remains, remains)
                remains += next_atm_input
                if next_need_encash != 0 and need_encash == 0:
                    remains = 0
                    remain_funding = []

                    for j in range(i, n):
                        j_atm_input = inputs[j]
                        j_funding_rate = funding_rates[j]

                        j_need_encash = calculate_encash(j_atm_input + remains, remains)
                        remains += j_atm_input

                        if j_need_encash != 0:
                            need_encash += j_need_encash
                            remains = j_need_encash + j_atm_input

                        remain_funding.append([remains, j_funding_rate])

                    next_need_encash = calculate_encash(next_atm_input + remains, remains)
                    remains += next_atm_input

                if next_need_encash != 0:
                    need_encash += next_need_encash
                    remains = next_need_encash + next_atm_input

                remain_funding.append([remains, next_funding_rate])

                n += 1

        funding_spending = 0
        remain_funding.reverse()
        for r_f in remain_funding:
            current_remain = r_f[0] + funding_spending
            current_funding = r_f[1]

            funding_spending += calculate_funding_cost(current_funding, current_remain)

        if need_encash != 0:
            need_encash += funding_spending

        result.append(need_encash)
        result_funding_spending = funding_spending

    return [result, result_funding_spending]


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

        inputs = []
        for date in dates:
            inputs.append(df_in.loc[df_in["atm_id"] == atm_id, date].values[0])

        funding_rates = []
        for date in dates:
            funding_rates.append(df_funding_rate.loc[df_funding_rate["value_day"] == date, "funding_rate"].values[0])

        permutations = get_worktime_permutations(dates, worktime)

        best_cost = -1
        best_result = []

        for permutation in permutations:

            encash_list_funding_remains = calculate_encash_result(remains, inputs, dates, permutation, funding_rates)

            encash_list = encash_list_funding_remains[0]
            funding_spending = encash_list_funding_remains[1]

            flag = False
            for encash in encash_list:
                if encash > 20000000 or encash < 0:
                    flag = True

            if flag:
                continue

            cost = total_cost(funding_spending, encash_cost, encash_list)

            if best_cost > cost or best_cost == -1:
                best_cost = cost
                best_result = encash_list

        write_to_df(df_res, atm_id, best_result, dates)

    df_res.to_csv("data_private.csv", index=None)


if __name__ == '__main__':
    main()
