#!/usr/bin/env python
# coding: utf-8

## Optimization Script
#### Importing Packages

import pandas as pd
import numpy as np
from math import floor
from datetime import timedelta
import matplotlib.pyplot as plt
from Backtesting_Class import Backtesting_Strategy

#### Definning variable

exit_target_sell = False
exit_range_sell = False
exit_hour_sell = False
exit_target_buy = False
exit_range_buy = False
exit_hour_buy = False

instrument = 'UNH'
hora_ini = '09:30:00'
hora_fin = '16:00:00'
tempo = 5
tempo_h = 1/12
account = 20000
risk = 0.01
profit_buy_pos = 0
profit_sell_pos = 0
profit_buy_neg = 0
profit_sell_neg = 0
exit_buy = 0
exit_sell = 0
total = []
final_results = []

## Bar Progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 3, length = 100, fill = '#'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()


## Resample Data
def resample_data (df, tempo_in, tempo_out):
    res = str(tempo_out)+'Min'
    
    if tempo_in < tempo_out:
        date = df.index
        Open = df.open.resample(res).first()
        High = df.high.resample(res).max()
        Low = df.low.resample(res).min()
        Close = df.close.resample(res).last()
        df_res = pd.concat([Open, High, Low, Close], axis = 1)
        df_res.columns = ['open', 'high', 'low', 'close']
        
        return (df_res)
    else:
        print('no fue posible hacer la conversion')
        return (df)

# Getting Data 
historical_0 = pd.read_csv(instrument+'_5secs.csv').set_index('date')
historical_0.index = pd.to_datetime(historical_0.index)
historical = historical_0
historical = resample_data(historical_0, 1/12, tempo_h).dropna()

# Setting the initial and final date to get days of evaluation

initial_date = '2018/06/08'
final_date = '2019/06/14'

delta = (pd.to_datetime(final_date) - pd.to_datetime(initial_date)).days + 1

dates = [str((pd.to_datetime(initial_date) + timedelta(days=x)).strftime("%Y/%m/%d")) for x in range(delta)]

# Setting variables to optimize
## target
start = 0.50
paso = 0.01
stop = 0.60

list_iter_target = np.round(list(np.arange(start,stop+paso,paso)),2)
print(list_iter_target)
len_ite_tar = len(list_iter_target)

## number of bars
start = 1
paso = 1
stop = 3

list_ite_num_bars = list(np.arange(start,stop+paso,paso))
print(list_ite_num_bars)
len_ite_num_bars = len(list_ite_num_bars)

## Temporality
list_ite_tempo = [tempo]
print(list_ite_tempo)
len_ite_tempo = len(list_ite_tempo)

total = pd.DataFrame(total)
final_results = pd.DataFrame(final_results)

total_iteration = len_ite_tempo*len_ite_num_bars*len_ite_tar*delta
iteration_0 = 0

# Main Code to calculate the Optimization results

for tempo in list_ite_tempo:   
    for num_bars in list_ite_num_bars:
        num_bars_h = int((num_bars*tempo)/tempo_h)
        for target_ite in list_iter_target:
            #printProgressBar(iteration_0 + 1, total_iteration, prefix = 'Progress:', suffix = 'Complete', length = 50)
            for date in dates:
                printProgressBar(iteration_0 + 1, total_iteration, prefix = 'Progress:', suffix = 'Complete', length = 50)
                
                #Getting the historical piece of data to evaluate
                hist = historical.loc[date,:]

                #Getting the max and mix from historical data. Calculating lots and target
                if (hist.empty == False):
                    maximum = hist.high.rolling(num_bars_h).max()[num_bars_h-1]
                    minimum = hist.low.rolling(num_bars_h).min()[num_bars_h-1]
                    range_tam = round(maximum - minimum,2)
                    target = target_ite
                    lots = floor((account*risk)/(maximum-minimum)) 
                else:
                    maximum = minimum = 0
                    range_tam = target = lots = 0
                    max_high = min_low = 0
                    exit_buy = exit_sell = 0
                    calc_sell = calc_buy = False

                #When to buy and sell
                hist['in_buy'] = hist['high'] > maximum
                hist['in_sell'] = hist['low'] < minimum

                if (hist.in_sell.sum() > 0):
                    calc_sell = True
                    price_sell = round(minimum - 0.02,2)
                    in_sell_bar = list(hist['in_sell'])
                    in_sell_bar = in_sell_bar.index(True)
                    highs_sell = hist.iloc[in_sell_bar:,1]
                    lows_sell = hist.iloc[in_sell_bar:,2]
                else:
                    calc_sell = False
                    price_sell = 0

                if (hist.in_buy.sum() > 0):
                    calc_buy = True
                    price_buy = round(maximum + 0.02,2)
                    in_buy_bar = list(hist['in_buy'])
                    in_buy_bar = in_buy_bar.index(True)
                    highs_buy = hist.iloc[in_buy_bar:,1]
                    lows_buy = hist.iloc[in_buy_bar:,2]
                else:
                    calc_buy = False
                    price_buy = 0

                #Determining when to exit
                ##sells
                if (calc_sell == True):    
                    for k in range(len(lows_sell)):
                        if (k == 0):
                            new_high_sells = highs_sell[k]
                            new_low_sells = lows_sell[k]
                        if (k > 0):
                            if (highs_sell[k] > new_high_sells):
                                new_high_sells = highs_sell[k]
                            if (lows_sell[k] < new_low_sells):
                                new_low_sells = lows_sell[k]

                        profit_sell_pos = round(price_sell - new_low_sells ,2)
                        profit_sell_neg = round(price_sell - new_high_sells , 2)
                        if (profit_sell_neg < -range_tam ):
                            profit_sell_neg = -range_tam

                        if (profit_sell_pos > target):
                            exit_target_sell = True
                            exit_sell = target
                        if (exit_target_sell == False) and (new_high_sells > maximum):
                            exit_range_sell = True
                            exit_sell = round(price_sell - maximum,2)
                        if (exit_target_sell == False) and (exit_range_sell == False) and (k == len(lows_sell)-1):
                            exit_hour_sell = True
                            exit_sell = round(price_sell - hist.iloc[-1,3],2)
                else:
                    exit_sell = 0
                    profit_sell_pos = 0
                    profit_sell_neg = 0

                ##buys
                if(calc_buy == True):    
                    for j in range(len(highs_buy)):
                        if (j == 0):
                            new_high_buys = highs_buy[j]
                            new_low_buys = lows_buy[j]
                        if(j > 0):
                            if (highs_buy[j] > new_high_buys):
                                new_high_buys = highs_buy[j]
                            if(lows_buy[j] < new_low_buys):
                                new_low_buys = lows_buy[j]

                        profit_buy_pos = round(new_high_buys - price_buy ,2)
                        profit_buy_neg = round(new_low_buys - price_buy, 2)
                        if (profit_buy_neg < -range_tam ):
                            profit_buy_neg = -range_tam

                        if (profit_buy_pos > target):
                            exit_target_buy = True
                            exit_buy = target
                        if (exit_target_buy == False) and (new_low_buys < minimum):
                            exit_range_buy = True
                            exit_buy = round(minimum - price_buy,2)
                        if (exit_target_buy == False) and (exit_range_buy == False) and (j == len(highs_buy)-1):
                            exit_hour_buy = True
                            exit_buy = round(hist.iloc[-1,3] - price_buy,2)
                else:
                    exit_buy = 0
                    profit_buy_pos = 0
                    profit_buy_neg = 0

                #Getting results
                results = [date, exit_buy, exit_sell, profit_buy_pos, profit_sell_pos, 
                           profit_buy_neg, profit_sell_neg, lots]
                results = pd.DataFrame(results).T.set_index(0)

                #Appending results
                total = pd.concat([total,results])

                #Restart variables in each iteration
                profit_buy_pos = profit_sell_pos = 0
                profit_buy_neg = profit_sell_neg = 0
                exit_buy = exit_sell = 0
                exit_target_sell = exit_range_sell = False
                exit_hour_sell = exit_target_buy = False
                exit_range_buy = exit_hour_buy = False
                calc_buy = calc_sell = False
                iteration_0+=1

            #Extern For cycle
            #Naming the total table
            total.index.names = ['date']
            total.columns = ['final profit buy', 'final profit sell', 'max profit buy', 'max profit sell', 'min profit buy', 'min profit sell', 'lots']
            #Profit by day
            total['profit usd'] = (total['final profit buy']+total['final profit sell'])*total['lots']
            #Accumulated Profit
            total['accumulated profit'] = total['profit usd'].cumsum() + account
            total['max profit'] = total['accumulated profit'].cummax()

            #Instantiating Backtesting Class
            back = Backtesting_Strategy(total)

            #--------- Results ---------
            
            #Net Profit -----------------------
            ##Total profit
            total_profit_usd = back.final_profit_usd()
            ##Total Commissions
            total_commissions = back.total_commissions()
            
            net_profit = total_profit_usd - total_commissions

            #Profit Factor -----------------------
            ##Gross Profit and Loss
            gross_profit, gross_loss = back.gross_profit_and_loss()
            
            profit_factor = round(abs(gross_profit/gross_loss),2)

            #Expected Payoff ---------------------------
            ##Number of trades
            total_trades, total_positive, total_negative, percent_total = back.transactions_info('total')
            
            expected_payoff = round(net_profit / total_trades,2)

            #Maximal Drawdown -----------------
            max_drawdown, max_draw_date = back.max_drawdown()

            #Relative Drawdown -------------------------
            relative_drawdown = round((max_drawdown/account)*100,2)

            #----------------------Final Results--------------------------------
            partial_results = [int(tempo), int(num_bars), target_ite, net_profit, profit_factor, 
                               expected_payoff, max_drawdown,relative_drawdown]
            partial_results = pd.DataFrame(partial_results).T.set_index(0)

            final_results = pd.concat([final_results,partial_results])

            #Restart variables-----------------------
            total = []
            total = pd.DataFrame(total)
            #iteration_0+=1

final_results.index.names = ['temporality']
final_results.columns = ['num of bars', 'target', 'net profit', 
                 'profit factor', 'expected payoff', 'max drawdown', 'relative drawdown']

final_results['profit_dd'] = final_results['net profit'] / final_results['max drawdown']

final_results.to_csv('results_'+instrument+'_5secs_'+str(tempo)+'min.csv')