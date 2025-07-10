import pandas as pd
import plotly.express as px
from typing import Tuple
from pathlib import Path


def display_bs(balance_sheet_list:Tuple[Path, Path], individual:bool = True) -> list:
    data = {"Name": ['Assets(資産)', 'Liabilities(負債)'],
            'CurrentLiabilities(流動負債)': [0, 0],
            'NoncurrentLiabilities(固定負債)': [0, 0],
            'CurrentAssets(流動資産)': [0, 0],
            'NoncurrentAssets(固定資産)': [0, 0],
            'NetAssets(純資産)': [0, 0],
            }

    bs_csv_list = []
    for balance_sheet in balance_sheet_list:
        for idx, path in enumerate(balance_sheet):
            df = pd.DataFrame.from_dict(data)

            temp_df = pd.read_csv(path)
            temp_df['要素ID_lower'] = temp_df['要素ID'].str.lower()

            temp_val = "個別" if individual else "連結"
            temp = temp_df[temp_df['連結・個別'] == temp_val]
            if temp.empty:
                print(f"{temp_val}が無いため{"個別" if not individual else "連結"}を使用")
                temp_val = "個別" if not individual else "連結"
                temp = temp_df[temp_df['連結・個別'] == temp_val]
            temp_df = temp.copy()
            del temp

            temp_df_assets = temp_df[temp_df['要素ID_lower'].str.contains("assets")]
            df.at[0, 'CurrentAssets(流動資産)'] = int(temp_df_assets[temp_df_assets['項目名'] == "流動資産"]['値'].values[0])
            df.at[0, 'NoncurrentAssets(固定資産)'] = int(temp_df_assets[temp_df_assets['項目名'] == "固定資産"]['値'].values[0])

            try:
                temp_val = "Prior1YearInstant_NonConsolidatedMember" if idx == 0 else "CurrentYearInstant_NonConsolidatedMember"
                df.at[1, 'NetAssets(純資産)'] = int(temp_df_assets[(temp_df_assets['項目名'] == "純資産")
                                                                    & (temp_df_assets['コンテキストID'] == temp_val)]['値'].values[0])
            except:
                temp_val = "Prior1YearInstant" if idx == 0 else "CurrentYearInstant"
                df.at[1, 'NetAssets(純資産)'] = int(temp_df_assets[(temp_df_assets['項目名'] == "純資産")
                                                                   & (temp_df_assets['コンテキストID'] == temp_val)][
                                                        '値'].values[0])

            temp_df_liability = temp_df[temp_df['要素ID_lower'].str.contains("liabilities")]
            df.at[1, 'CurrentLiabilities(流動負債)'] = int(temp_df_liability[temp_df_liability['項目名'] == "流動負債"]['値'].values[0])
            df.at[1, 'NoncurrentLiabilities(固定負債)'] = int(temp_df_liability[temp_df_liability['項目名'] == "固定負債"]['値'].values[0])

            fig = px.bar(df, x="Name", y=list(data.keys())[1:], title=f"BS {"(前期)" if idx == 0 else "(当期)"} {"個別" if individual else "連結"}")
            fig.show()

            bs_csv_list.append(df)

        return bs_csv_list