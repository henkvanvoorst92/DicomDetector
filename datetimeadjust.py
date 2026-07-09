
import pandas as pd
from tqdm import tqdm

def get_datetime_column(
        tmp:pd.DataFrame or pd.Series,
        datetimevars=('AcquisitionDateTime',
                      'ContentDateTime',
                      'SeriesDateTime')):
    """
    Returns
    -------
    datetimevar : str
        Name of the datetime column used/created.
    dt : pd.Series
        Datetime values.
    """

    for datetimevar in datetimevars:

        # Try constructing from Date + Time columns
        datevar = datetimevar.replace('Time', '')
        timevar = datetimevar.replace('Date', '')

        done = False
        if isinstance(tmp, pd.DataFrame) and len(tmp) == 1:
            tmp = tmp.squeeze()

        if isinstance(tmp, pd.DataFrame):
            if datetimevar in tmp.columns:
                tmp[datetimevar] = pd.to_datetime(tmp[datetimevar], errors='coerce')
                if not pd.isna(tmp[datetimevar]):
                    done = True

            if datevar in tmp.columns and timevar in tmp.columns and not done:
                    time_vals = [("000000" + str(tmp[tv]).split('.')[0])[-6:] for tv in tmp[timevar]]

                    tmp[datetimevar] = pd.to_datetime(
                                            tmp[datevar].astype(str).str.replace('.0', '', regex=False)
                                            + time_vals,
                                            format='%Y%m%d%H%M%S', #.%f
                                            errors='coerce')
                    if not pd.isna(tmp[datetimevar]):
                        done = True

            if not done:
                continue

            tmp = tmp.sort_values(datetimevar).reset_index(drop=True)

            return datetimevar, tmp

        elif isinstance(tmp, pd.Series):
            if datetimevar in tmp.index:
                tmp[datetimevar] = pd.to_datetime(tmp[datetimevar], errors='coerce')
                if not pd.isna(tmp[datetimevar]):
                    done = True

            if datevar in tmp.index and timevar in tmp.index and not done:
                if isinstance(tmp[timevar], str):
                    time_vals = ("000000" + str(tmp[timevar]).split('.')[0])[-6:]
                else:
                    time_vals = [("000000" + str(tmp[tv]).split('.')[0])[-6:] for tv in tmp[timevar]]
                if isinstance(tmp[datevar], str):
                    tmp[datetimevar] = pd.to_datetime(
                        str(tmp[datevar]).replace('.0', '')
                        + time_vals,
                        format='%Y%m%d%H%M%S',  # .%f
                        errors='coerce')
                else:
                    tmp[datetimevar] = pd.to_datetime(
                        tmp[datevar].astype(str).str.replace('.0', '', regex=False)
                        + time_vals,
                        format='%Y%m%d%H%M%S',  # .%f
                        errors='coerce')

                if not pd.isna(tmp[datetimevar]):
                    done = True

            if not done:
                continue
            tmp['datetimevar'] = datetimevar
            return datetimevar, tmp


def pd_redo_timestamp(df):
    if isinstance(df, pd.Series):
        df = df.to_frame().T

    out = []
    for ID,row in tqdm(df.iterrows()): #, desc='Redoing timestamps'
        if 'AcquisitionDateTime' in row.index:
            if isinstance(row['AcquisitionDateTime'], pd.Timestamp):
                row['datetimevar'] = 'AcquisitionDateTime'
        try:
            dtvar,row = get_datetime_column(row,
                                datetimevars=('AcquisitionDateTime',
                                              'ContentDateTime',
                                              'SeriesDateTime'))
            row['datetimevar'] = dtvar

        except:
           #print(f'Could not find datetime for {ID}')
           row['datetimevar'] = None
        if 'ID' not in row:
            row['ID'] = ID
        out.append(row)

    return pd.DataFrame(out)

