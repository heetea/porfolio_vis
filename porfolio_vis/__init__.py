#!/usr/bin/env python
# Portfolio Back testing Library
# Copyright (c)  Heaatea Roh
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import as_strided as stride
import porfolio_vis.cal_return
import porfolio_vis.get_data
import porfolio_vis.report
from tqdm import tqdm


class strategy:
    def __init__(self,data_list, country, window_hold='Q', rebalancing_date=-5):
        self.data_list = data_list
        self.country = country
        self.data = self.load_data(data_list)
        self.window_hold = window_hold
        self.rebalancing_date = rebalancing_date
        self.date_list = self.get_date_list(self.window_hold, self.rebalancing_date)
    def load_data(self, data_list):
        print('데이터 크롤링 중')
        if self.country =='kr':
            answer = pd.DataFrame()
            for name in tqdm(data_list):
                answer[name] = portvis.get_data.get_naver_close(name)[name]
            answer.index.name='date'
            return answer
        elif self.country =='us':
            answer = get_data.get_data_yahoo_close(data_list)
            answer.index.name='date'
            return answer

        else:
            print('테스트 가능한 국가가 아닙니다')
    def get_date_list(self, window_hold='Q', rebalancing_date=-5):
        w = self.data[self.data.index.hour != 9].iloc[:, :1]
        w['period'] = w.index.to_period(window_hold)
        w = w.reset_index().groupby('period').nth(rebalancing_date)['date']
        return list(w)
    # 그룹 만들기
    def get_group(self, window_fit, **kwargs):
    # 월별, 연도별, 쿼터별 window fit
        if window_fit in ['D','M','Q','Y','W']:
            if window_fit =='D':
                period = pd.DateOffset(days=1)
            elif window_fit == 'M':
                period = pd.DateOffset(months=1)
            elif window_fit == 'Q':
                period = pd.DateOffset(months=3)
            elif window_fit == 'Y':
                period = pd.DateOffset(months=12)
            elif window_fit == 'W':
                period = pd.DateOffset(weeks=1)
            limit = self.data.index[0] + period
            df_list = []

            for date in self.date_list:
                if date > limit:
                    temp = self.data[date-period :date]
                    temp.index = pd.MultiIndex.from_tuples([(temp.index[-1],num) for num in range(len(temp.index))])
                    df_list.append(temp)
                else:
                    pass

        else:
            v = self.data.values
            d0, d1 = v.shape
            s0, s1 = v.strides
            a = stride(v, (d0 - (window_fit - 1), window_fit, d1), (s0, s0, s1))
            df_list = []
            for row, values in zip(self.data.index[window_fit:], a):
                temp = pd.DataFrame(values, columns=self.data.columns)
                if row in self.date_list:
                    temp.index = pd.MultiIndex.from_tuples([(row, num) for num in temp.index])
                    df_list.append(temp)
                else:
                    pass
        rolled_df = pd.concat(df_list)
        group = rolled_df.groupby(level=0, **kwargs)

        return group
    def get_return(self, ratio_df, cost=None):
        ratio_df = ratio_df.replace(0,np.nan).dropna(1,'all').fillna(0)
        price = self.data.copy()[ratio_df.columns]
        cls = cal_return.cal_return(price.pct_change(), ratio_df)
        if cost==None:
            ans = cls.compound_return()
        else:
            ans = cls.cost_cumpound_return(cost)
        return ans
    def action(self, func, window_fit, cost=None):
        gr = self.get_group(window_fit)
        df = gr.apply(func)
        ans = self.get_return(df, cost=cost)
        return ans
    def func(self, state, ratio):
        answer = state.iloc[0].copy()
        answer.loc[answer.index] = ratio
        return answer


def action(data_list,ratio_list, country, window_hold='Q', rebalancing_date=-5,window_fit='Q', cost=None):
    cls = strategy(data_list, country, window_hold, rebalancing_date)
    gr = cls.get_group(window_fit)
    df = gr.apply(cls.func, ratio_list)
    df.index.name = 'date'
    ans = cls.get_return(df, cost=cost)
    report_cls = report.Portfolio(ans)
    report_cls.report()

