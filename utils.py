import requests
import json
import pandas as pd
from pathlib import Path
import zipfile
from typing import Tuple
import io
import time


class GetData:
    def __init__(self, EDINET_API:str) -> None:
        self.api = EDINET_API


    def get_company_meta_data(self, get_date:str) -> json:
        '''EDINETから会社の情報の習得

        :param get_date: str:
        :return: json
        '''

        # APIのエンドポイント
        url = 'https://disclosure.edinet-fsa.go.jp/api/v2/documents.json'

        # パラメータの設定
        params = {
            'date': get_date,
            'type': 2,  # 2は有価証券報告書などの決算書類
            "Subscription-Key": self.api
        }

        # APIリクエストを送信
        response = requests.get(url, params=params)

        # レスポンスのJSONデータを取得
        return response.json()


    def create_csv(self, get_date:str) -> pd.DataFrame:
        '''EDINETから会社の情報をPandasに変換

        :param get_date:
        :return: pd.DataFrame
        '''

        json_data = self.get_company_meta_data(get_date)
        return pd.DataFrame(json_data["results"])


    def get_finance_data(self, id_name_list:list) -> Tuple[Path, Path]:
        file_path_list = []
        max_retries = 3

        for id in id_name_list:
            url = f"https://disclosure.edinet-fsa.go.jp/api/v2/documents/{id}"
            params = {"type": 5,  # csvは５
                      "Subscription-Key":self.api}

            if not Path('./company_finance_data').exists():
                Path('./company_finance_data').mkdir()

            if not Path(f'./company_finance_data/{id}').exists():
                Path(f'./company_finance_data/{id}').mkdir()

            file_path = Path(f'./company_finance_data/{id}/')
            for attempt in range(max_retries):
                try:
                    res = requests.get(url, params=params, verify=False)
                    res.raise_for_status()
                    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                        for file in z.namelist():
                            if file.startswith("XBRL_TO_CSV/jpcrp") or file.startswith("XBRL_TO_CSV/jpsps"):
                                if file.endswith(".csv"):
                                    z.extract(file, file_path)
                    time.sleep(5)  # 適切な待機時間を設定

                    # ファイルをPriorとCurrentに分けて保存
                    prior_save_path, current_save_path = self.split_data_with_prior_current(file_path / file)
                    file_path_list.append([prior_save_path, current_save_path])

                except Exception as e:
                    print(f"エラーが発生しました {id}: {e}")
                    if attempt < max_retries - 1:
                        print(f"{5}秒後に再挑戦します...")
                        time.sleep(5)
                break

        return file_path_list


    def split_data_with_prior_current(self, file_path:Path) -> Tuple[Path, Path]:
        """ダウンロードしたCSVをPriorとCurrentに分けて、保存する

        :param file_path:
        :return: Tuple[Path, Path]
        """

        df = pd.read_csv(file_path, encoding="utf-16", sep="\t")
        prior_df = df[df['コンテキストID'].str.contains("Prior")]
        prior_save_path = Path(file_path.parent / f'prior_{file_path.stem}.csv')
        prior_df.to_csv(prior_save_path, index=False)

        current_df = df[~df['コンテキストID'].str.contains("Prior")]
        current_save_path = Path(file_path.parent / f'current_{file_path.stem}.csv')
        current_df.to_csv(current_save_path, index=False)

        return prior_save_path, current_save_path
