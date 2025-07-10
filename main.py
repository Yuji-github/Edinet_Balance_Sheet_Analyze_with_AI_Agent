from api_config import EDINET_API, HF_API_KEY
from utils import GetData
from display import *
from llm_analyzer import LLMAnalyzer
from datetime import datetime
import argparse
import pandas as pd
import warnings
from pathlib import Path


def parse_args() -> argparse:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--docid",
        "-di",
        type=str,
        help="書類管理番号",
        required=False,
    )
    parser.add_argument(
        "--company_name",
        "-cn",
        type=str,
        default="明治安田アセットマネジメント株式会社",
        help="会社名",
        required=False,
    )
    parser.add_argument(
        "--individual",
        "-ind",
        type=eval,
        choices=[True, False],
        help="連結・個別　（個別がディフォルト）",
        default=True,
        required=False,
    )
    parser.add_argument(
        "--get_date",
        "-gd",
        type=str,
        help="習得したい日：　ない場合は本日のデータ使用: フォーマット '%Y-%m-%d'",
        required=False,
    )

    return parser.parse_args()


if __name__ == '__main__':

    if EDINET_API is None:
        warnings.warn("EDINET API がありません：　https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1")
        warnings.warn("APIを習得してapi_config.pyに保存してください: EDINET_API = 習得したAPI")
        exit()

    if HF_API_KEY is None:
        warnings.warn("HuggingFace API KEY がありません：")
        warnings.warn("APIを習得してapi_config.pyに保存してください: HF_API_KEY = 習得したAPI")
        exit()

    args = parse_args()
    docid = args.docid
    company_name = args.company_name

    if not docid and not company_name:
        if not docid:
            warnings.warn("docID(書類管理番号)がありません")
        else:
            warnings.warn("会社名がありません")
        warnings.warn("docID(書類管理番号)か会社名のどちらかを与えてください。")
        exit()

    get_data_utilis = GetData(EDINET_API)

    if not docid:
        # 会社の情報の習得
        if not Path('./company_csv_folder').exists():
            Path('./company_csv_folder').mkdir()

        if args.get_date:
            temp_get_date = datetime.strptime(args.get_date, '%Y-%m-%d')
            if datetime.today() < temp_get_date:
                get_date = datetime.today().strftime('%Y-%m-%d')
            else:
                get_date = temp_get_date.strftime('%Y-%m-%d')
        else:
            get_date = datetime.today().strftime('%Y-%m-%d')

        if Path(f'./company_csv_folder/data_{get_date}.csv').exists():
            df = pd.read_csv(f'./company_csv_folder/data_{get_date}.csv')
        else:
            df = get_data_utilis.create_csv(get_date)

        # 会社のdocid(書類管理番号)の習得
        docid = df[df['filerName'] == company_name]['docID']
        if docid.empty:
            all_dfs = [data for data in Path('./company_csv_folder/').rglob("data_*.csv")]
            for path in all_dfs:
                temp = pd.read_csv(path)
                docid = temp[temp['filerName'] == company_name]['docID']
                if not docid.empty:
                    break
        df.to_csv(f'./company_csv_folder/data_{get_date}.csv', index=False)

    if len(docid) == 0:
        warnings.warn("書類管理番号(docID)が見つかりません。会社名を使い検索します。")
        warnings.warn("会社名が正しくない場合、データ取得が出来ない場合があります。")

    search_data = []
    if len(docid) != 0:
        if type(docid) is str:
            search_data.append(docid)
        else:
            search_data = docid.tolist()
    else:
        search_data.append(company_name)

    finance_csv_list = get_data_utilis.get_finance_data(search_data)
    result_list = display_bs(finance_csv_list, args.individual)

    agent = LLMAnalyzer(HF_API_KEY)
    agent.agent_analyze(result_list)