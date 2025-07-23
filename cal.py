def cal_results(result_list):
    df = result_list

    na = sum(df[0]['NetAssets(純資産)'])
    ncl = sum(df[0]['NoncurrentLiabilities(固定負債)'])
    cl = sum(df[0]['CurrentLiabilities(流動負債)'])
    nca = sum(df[0]['NoncurrentAssets(固定資産)'])
    ca = sum(df[0]['CurrentAssets(流動資産)'])

    total_assets = nca + ca #総資産
    total_liabilities = ncl + cl #総負債

    current_ratio = (ca / cl ) * 100  # １００％以上が良い
    equity_ratio = (na / total_assets) * 100 #　５０％以上で良い
    fixed_ratio = (nca/na) * 100 #１００％以下が望ましい（業種による）

    print(f"前期流動比率は{round(current_ratio,2)}%")
    print(f"前期自己資本比率は{round(equity_ratio,2)}%")
    print(f"前期固定比率は{round(fixed_ratio,2)}%")


    t_na = sum(df[1]['NetAssets(純資産)'])
    t_ncl = sum(df[1]['NoncurrentLiabilities(固定負債)'])
    t_cl = sum(df[1]['CurrentLiabilities(流動負債)'])
    t_nca = sum(df[1]['NoncurrentAssets(固定資産)'])
    t_ca = sum(df[1]['CurrentAssets(流動資産)'])


    t_total_assets = t_nca + t_ca
    t_total_liabilities = t_ncl + t_cl

    t_current_ratio = (t_ca / t_cl) * 100
    t_equity_ratio = (t_na / t_total_assets) * 100
    t_fixed_ratio = (t_nca / t_na) * 100

    print(f"当期流動比率は{round(t_current_ratio, 2)}%")
    print(f"当期自己資本比率は{round(t_equity_ratio, 2)}%")
    print(f"当期固定比率は{round(t_fixed_ratio, 2)}%")

