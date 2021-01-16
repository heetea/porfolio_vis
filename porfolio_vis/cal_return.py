import pandas as pd
import numpy as np

class cal_return:
    def __init__(self, day_yield, periodic_weight):
        self.df = day_yield
        self.day_yield =day_yield
        self.periodic_weight = periodic_weight
        self.period = pd.to_datetime(periodic_weight.index)


    def compound_return(self):
        df = self.day_yield.copy()

        df.loc[self.period] = 0
        df.loc[self.period,'period'] = range(len(self.period))

        df['period'] = df['period'].fillna(method='ffill')

        temp = df.groupby('period').apply(self.get_return)
        temp = temp.cumprod().reset_index()
        temp.index = temp['date']

        df = temp[[0]]
        df.columns = ['price']
        df = df / df.iloc[0]
        return df
    def get_return(self, state):
        state = state.drop('period',axis=1)
        ans = (state+1).cumprod()
        period = self.periodic_weight.loc[state.index[0]]

        temp = (period*ans).sum(1)

        ans = temp.pct_change()
        ans.iloc[0] = temp.iloc[0]/1-1
        ans = ans+1
        return ans
    def port_changed_func(self,state):
        state = state.drop('period', axis=1)
        ans = (state + 1).cumprod()
        period = self.periodic_weight.loc[state.index[0]]
        temp = (period * ans)
        return (temp.iloc[-1]) / temp.iloc[-1].sum()
    def cost_cumpound_return(self,cost):
        df = self.day_yield.copy()
        df.loc[self.period, 'period'] = range(len(self.period))
        df['period'] = df['period'].fillna(method='ffill')

        temp = df.groupby('period').apply(self.get_return).reset_index()
        temp2 = df.groupby('period').apply(self.port_changed_func)

        temp3 = self.periodic_weight.copy()
        temp3.index = temp2.index

        temp.loc[temp.groupby('period')[0].head(1).index, 0] = list(temp.groupby('period')[0].first() * (1 + abs(temp2 - temp3).sum(1) * (-cost)))
        temp = temp.set_index('date')[[0]]
        temp.columns = ['price']
        ans = temp.cumprod()
        return ans
    def get_stastics(self):
        from matplotlib import pyplot as plt
        df = self.day_yield.copy()

        df.loc[self.period] = 0
        df.loc[self.period, 'period'] = range(len(self.period))

        df['period'] = df['period'].fillna(method='ffill')
        df = df[df['period']!=df['period'].max()]
        max_num = df['period'].value_counts().max()
        temp = df.groupby('period').apply(self.st)
        temp['period'] = df['period']

        ans = pd.Series()
        for i in range(max_num):
            ans[f'{i}'] = temp.groupby('period').nth(i).stack().mean()
        ans.plot(title='보유후 n일후 수익률')
        plt.show()
        return ans
    @staticmethod
    def st(state):
        state = state.drop('period', axis=1)
        ans = np.log((state + 1).cumprod())
        return ans
