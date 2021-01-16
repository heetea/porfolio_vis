# Using graph_objects
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = "browser"
import pandas as pd
import numpy as np
from bokeh.plotting import figure, output_file, show, curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import column, row, widgetbox
from bokeh.models.widgets import *
from bokeh.models import Legend, Column
from bokeh import palettes
class Portfolio:
    def __init__(self, price):
        price.index = pd.to_datetime(price.index)
        price = price.dropna()

        self.price = price
        self.pct = price.pct_change().fillna(0)
        year_dates = self.price.groupby(self.price.index.year).count()
        if len(year_dates) <=2:
            self.year_dates = 250
        else:
            self.year_dates = year_dates.iloc[1:-1].mean().iloc[0]

        self.cumsum_sr = self.pct.cumsum() +1
        self.compound_sr = (self.pct+1).cumprod()
        self.cumsum = self.cumsum_sr.iloc[-1]
        self.compound = self.compound_sr.iloc[-1]
        self.dd = self.get_dd(self.price)
        self.mdd = self.dd.min()
        self.cagr = self.get_cagr(self.compound_sr, self.year_dates)
        self.sharpe = self.get_sharpe(self.pct, self.year_dates)
        self.color_list = ['#ec008e', '#361b6f', '#0086d4', '#8c98a0'] + list(palettes.Category20_20)
    @staticmethod
    def get_dd(price):
        return price/price.expanding().max() -1
    @staticmethod
    def get_cagr(compound_sr, year_dates):
        return compound_sr.iloc[-1]**(year_dates/compound_sr.shape[0])-1
    @staticmethod
    def get_sharpe(pct, year_dates):
        return ((1 + pct.mean()) ** year_dates - 1)/(pct.std() * np.sqrt(year_dates))
    def report(self, simple=False, output_name='제목없음'):
        output_file(output_name + '.html')
        def to_source(df):
            df.index = pd.to_datetime(df.index, format="%Y-%m-%d")
            return ColumnDataSource(df)
        static_data = pd.concat(
            [self.compound, self.cagr, self.sharpe, self.mdd],
            axis=1)
        static_data.columns = ['Compound_Return', 'CAGR', 'Sharpe Ratio', 'MDD']

        for col in static_data.columns:
            if col in ['Simple_Return', 'CAGR', 'MDD', 'Average Drawdown', 'Standard Deviation']:
                # if col in ['Cumulative_Return', 'CAGR', 'MDD', 'Average Drawdown']:
                static_data.loc[:, col] = static_data.loc[:, col].apply(
                    lambda x: str(np.around((x * 100), decimals=2)) + "%")
            else:
                static_data.loc[:, col] = static_data.loc[:, col].apply(lambda x: np.around(x, decimals=4))

        static_data.reset_index(inplace=True)
        static_data.rename(columns={'index': 'Portfolio'}, inplace=True)
        source = ColumnDataSource(static_data)
        columns = [TableColumn(field=col, title=col) for col in static_data.columns]
        data_table = DataTable(source=source, columns=columns, width=1500, height=200, index_position=None)
        if simple:
            # Plot 단리
            source = to_source(self.cumsum_sr)
            source_for_chart = to_source(self.cumsum_sr - 1)
            p1 = figure(x_axis_type='datetime',
                        title='Simple Return' + f'({self.cumsum_sr.index[0].strftime("%Y-%m-%d")} ~ {self.cumsum_sr.index[-1].strftime("%Y-%m-%d")})',
                        plot_width=1500, plot_height=400, toolbar_location="above")
        elif simple=='log':
            # Plot 로그
            source = to_source(self.compound_sr)
            source_for_chart = to_source(self.compound_sr)

            p1 = figure(x_axis_type='datetime', y_axis_type='log',
                        title='Log Compound Return' + f'({self.compound_sr.index[0].strftime("%Y-%m-%d")} ~ {self.compound_sr.index[-1].strftime("%Y-%m-%d")})',
                        plot_width=1500, plot_height=450, toolbar_location="above")

        else:
            # Plot 복리
            source = to_source(self.compound_sr)
            source_for_chart = to_source(self.compound_sr - 1)

            p1 = figure(x_axis_type='datetime',
                        title='Compound Return' + f'({self.compound_sr.index[0].strftime("%Y-%m-%d")} ~ {self.compound_sr.index[-1].strftime("%Y-%m-%d")})',
                        plot_width=1500, plot_height=450, toolbar_location="above")



        legend_list = []
        for i, col in enumerate(self.compound_sr.columns):
            p_line = p1.line(source=source_for_chart, x='date', y=col, color=self.color_list[i], line_width=2)
            legend_list.append((col, [p_line]))
        legend = Legend(items=legend_list, location='center')

        # Plot drawdown
        source_p3 = to_source(self.dd)
        p3 = figure(x_axis_type='datetime',
                    title='Drawdown',
                    plot_width=1500, plot_height=170, toolbar_location="above")
        legend_list = []
        for i, col in enumerate(self.dd.columns):
            # p3.line(source=source, x='date', y=col, color=color_list[i], legend=col + " Drawdown")
            baseline = np.zeros_like(self.dd[col].values)
            y = np.append(baseline, self.dd[col].values[::-1])
            x = self.dd.index.values
            x = np.append(x, x[::-1])

            p_line = p3.line(source=source_p3, x='date', y=col, color=self.color_list[i], line_width=2)
            legend_list.append((col, [p_line]))
        legend_3 = Legend(items=legend_list, location='center')

        p1.add_layout(legend, 'right')
        p1.legend.click_policy = "hide"

        p3.add_layout(legend_3, 'right')
        p3.legend.click_policy = "hide"

        from bokeh.models import NumeralTickFormatter
        p1.yaxis.formatter = NumeralTickFormatter(format='0 %')
        p3.yaxis.formatter = NumeralTickFormatter(format='0 %')

        show(column(p1, p3, Column(data_table)))



