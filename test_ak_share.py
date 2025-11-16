import akshare as ak


# 实时行情数据-新浪
# stock_zh_a_spot_df = ak.stock_zh_a_spot()
# print(stock_zh_a_spot_df)


# 个股实时行情数据-雪球
# stock_individual_spot_xq_df = ak.stock_individual_spot_xq(symbol="SH600000")
# print(stock_individual_spot_xq_df)

# 个股基本信息-雪球
# stock_individual_basic_info_xq_df = ak.stock_individual_basic_info_xq(symbol="SH601088")
# print(stock_individual_basic_info_xq_df)

# 个股信息查询-东财
# stock_individual_info_em_df = ak.stock_individual_info_em(symbol="000001")
# print(stock_individual_info_em_df)

# 历史行情数据-东财
# stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20240528', adjust="")
# print(stock_zh_a_hist_df)

# 历史行情数据-新浪
# stock_zh_a_daily_qfq_df = ak.stock_zh_a_daily(symbol="sz000001", start_date="19910403", end_date="20231027", adjust="qfq")
# print(stock_zh_a_daily_qfq_df)

# 历史交易数据-腾讯
stock_zh_a_hist_tx_df = ak.stock_zh_a_hist_tx(symbol="sz000001", start_date="20200101", end_date="20251114", adjust="qfq")
print(stock_zh_a_hist_tx_df)