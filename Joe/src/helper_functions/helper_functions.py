def calc_yearly_percent_change(x):
    yearly_inc = []
    for i in range(len(x)):
        if i == 0:
            j = 0
        else:
            j = i - 1
        inc = (x[i]-x[j]) / x[j]
        yearly_inc.append(inc)
    return yearly_inc

def set_index(df, column):
    df.set_index(column, inplace=True)
    return df

def calc_yearly_change(x):
    yearly_inc = []
    for i in range(len(x)):
        if i == 0:
            j = 0
        else:
            j = i - 1
        inc = (x.iloc[i]-x.iloc[j])
        yearly_inc.append(inc)
    return yearly_inc