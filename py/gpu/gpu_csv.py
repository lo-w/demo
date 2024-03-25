from datetime import datetime
import cudf

def output_csv(data, unit, c='count'):
    ct = data[unit].value_counts().to_frame(name=c)
    rf = data.merge(ct, left_on=unit, right_index=True, how='left').sort_index()
    rs = rf.drop_duplicates(subset=unit, keep="first", inplace=False)
    print('sort finish:', datetime.now())
    rs.to_csv('./%s.csv' % unit, index=False)

def merge_table(p, unit='hour'):
    print('start time:', datetime.now())
    cf = cudf.read_csv(p, usecols=[2,3,4,11])
    print('read finish:', datetime.now())
    if unit == 'hour':
        f = '%Y-%m-%d %H'
    elif unit == 'min':
        f = '%Y-%m-%d %H:%M'
    else:
        f = '%Y-%m-%d %H:%M:%S'
    cf['hour'] = cudf.to_datetime(cf['create_time_x'], format=f)
    output_csv(cf, unit)
    print('end time:', datetime.now())

merge_table('./test.csv.bak')
