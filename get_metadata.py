

import os
import pydicom
import pandas as pd
from tqdm import tqdm
import warnings
#warnings.filterwarnings("ignore", message="The value length *")
warnings.filterwarnings("ignore")

from metadata import complete_tag_values, get_tag_value
from multiframe import n_same_position_from_dicom
from datetimeadjust import get_datetime_column, pd_redo_timestamp
from modality_finder import dwi_identifier, perf_identifier, ncct_identifier, cta_identifier
from utils import combine_excel_files, make_columns_unique
from utils import get_general_args
from multiprocessing import Pool


def chunk_jobs(input_dir, output_dir, jobs, file_limits=(0,1e6), multipos_limits=(1,12), skip_tags=['Privatetagdata'], export_to='.xlsx'):
    """
    Batch process files in the input directory using the specified number of jobs.

    file_limits: tuple (min_files, max_files) to filter directories based on the number of files.
    multipos_limits: tuple (min_mpos, max_mpos) to filter directories based on the number of same position slices

    """
    if not os.path.exists(input_dir):
        raise ValueError(f"Input directory does not exist: {input_dir}")

    if output_dir is not None:
        IDs_done = [f.split('_')[0] for f in os.listdir(output_dir) if f.endswith(f'_metadata{export_to}')]
    else:
        IDs_done = []

    inp = []
    for ID in os.listdir(input_dir):
        pid = os.path.join(input_dir, ID)
        if not os.path.isdir(pid):
            continue
        if ID in IDs_done:
            continue
        inp.append((ID, pid))

    chunk_size = len(inp) // jobs + (len(inp) % jobs > 0)
    jobs = [(inp[i:i + chunk_size], output_dir, file_limits, multipos_limits, skip_tags, export_to) for i in range(0, len(inp), chunk_size)]

    return jobs

def process_dcmdir(root, fix=10, n_same_position=None, skip_tags=['Privatetagdata'], unique_dirno=None, ID=None, pid=None):
    #extracting info from single dicom directory

    file10 = os.path.join(root, os.listdir(root)[fix])
    dcm = pydicom.dcmread(file10, stop_before_pixels=True)
    tmp = complete_tag_values(dcm, skip_tags=skip_tags)
    tmp['dirno'] = unique_dirno
    tmp['dcmfile'] = file10
    tmp['ID'] = ID
    tmp['pid'] = pid.replace('/mnt/newstroke/', '').replace('/mnt/stroke/', '')
    tmp['scandir'] = root.replace('/mnt/newstroke/', '').replace('/mnt/stroke/', '')
    tmp['nfiles'] = len(os.listdir(root))
    if n_same_position is None:
        tmp['same_position_number'] = n_same_position_from_dicom(root, fix=fix)
    else:
        tmp['same_position_number'] = n_same_position

    if isinstance(tmp, pd.Series):
        tmp = tmp.to_frame().T
    return tmp

def all_series_of_ID(ID, p_in, f_out=None, file_limits=(0, 1e6), multipos_limits=(1, 12), skip_tags=['Privatetagdata']):
    """
    Returns a list of all series directories for a given ID that meet the file and multipos limits.
    """
    min_files, max_files = file_limits
    min_mpos, max_mpos = multipos_limits

    pid = os.path.join(p_in, ID)
    if not os.path.isdir(pid):
        return None

    unique_dirno = 0
    scan_mdata = []
    for root, drs, files in os.walk(pid):
        #iterates over series folders
        #skips fewer than min_files or more than max_files files
        #skips fewer than min_mpos or more than max_mpos same position slices
        try:
            if len(files) < min_files or len(files) > max_files:
                continue
            n_same_position = n_same_position_from_dicom(root, fix=min_files - 1)
            if n_same_position < min_mpos or n_same_position > max_mpos:
                continue
            #processes unique dicom series
            tmp = process_dcmdir(root,
                                 fix=min_files - 1,
                                 n_same_position=n_same_position, #if not a number given is calculated
                                 skip_tags=skip_tags, #tags to skip (generally hiddern causing errors)
                                 unique_dirno=unique_dirno, #may be skipped
                                 ID=ID, pid=pid) #ID is vital for finding later
            unique_dirno += 1

            if tmp.columns.has_duplicates:
                tmp.columns = make_columns_unique(tmp.columns)

            scan_mdata.append(tmp)
        except Exception as e:
            print(f"Error processing {root}: {e}")
            continue

    try:
        if len(scan_mdata) == 0:
            raise ValueError(f"No valid series found for ID {ID} in {pid} with the given file and multipos limits.")
        elif len(scan_mdata) == 1:
            mdata = scan_mdata[0]
        elif len(scan_mdata) > 1:
            mdata = pd.concat(scan_mdata, ignore_index=True).reset_index(drop=True)

        # adds the required datetime metadata if needed and sorts chronologically
        mdata = pd_redo_timestamp(mdata)
        mdata['DateTimeSelected'] = mdata.apply(lambda row: row.get(row.get("datetimevar"), None), axis=1)
        mdata.sort_values(by=['DateTimeSelected'], inplace=True, na_position='last')
        # identify likely DWI
        mdata = dwi_identifier(mdata, n_same_pos=(2, 14))
        # identify likely CTP and PWI
        mdata = perf_identifier(mdata, n_same_pos=(14, 1e6))
        # NCCT identifier
        mdata = ncct_identifier(mdata)
        # CTA identifier
        mdata = cta_identifier(mdata)

        if f_out is not None:
            if f_out.endswith('.xlsx'):
                mdata.to_excel(f_out, index=False)
            elif f_out.endswith('.pic'):
                mdata.to_pickle(f_out)
            else:
                raise ValueError(f"Unsupported file extension for output: {f_out}")
    except Exception as e:
        print(f"Error processing metadata for ID {ID}: {e}")

    return mdata

def get_all_metadata(inp,
                     p_out,
                     file_limits=(0, 1e6),
                     multipos_limits=(1, 12),
                     skip_tags=['Privatetagdata'],
                     timetag=None,
                     overwrite=False,
                     export_to='.xlsx'):
    """
    Processing of entire directory with ID subdirs

    p_in: first folder should be ID, remainder dicom data dump
    p_out: output location for metadata
    file_limits: only folders in p_in within the file_limites are considered
    multipos_limits: only folders in p_in within the multipos_limits (number of volumes with same position) are considered
    skip_tags: dicom tags to skip when extracting metadata
    """
    min_files, max_files = file_limits
    min_mpos, max_mpos = multipos_limits
    os.makedirs(p_out, exist_ok=True)

    if isinstance(inp, str):
        inp = [(ID, os.path.join(inp,ID)) for ID in os.listdir(inp) if os.path.isdir(os.path.join(inp, ID))]

    for (ID, pid) in tqdm(inp):
        if not os.path.isdir(pid):
            continue
        f_out = os.path.join(p_out, f'{ID}_metadata{export_to}')
        if os.path.exists(f_out) and not overwrite:
            continue
        try:
            mdata = all_series_of_ID(ID, p_in=os.path.dirname(pid),
                                     f_out=f_out,
                                     file_limits=file_limits,
                                     multipos_limits=multipos_limits,
                                     skip_tags=skip_tags)
        except Exception as e:
            print(e)
            print(f'Error processing {pid}')
            continue

def get_full_combined(dir_outputs, f_out=None, incl_string='_metadata.xlsx', redo_timestamps=False, redo_labelling=False):
    if f_out is None:
        f_out = os.path.join(os.path.dirname(dir_outputs), 'combined_metadata.xlsx')
    if not os.path.exists(f_out):
        df = combine_excel_files(dir_outputs, incl_string=incl_string, verbose=True)
        #df = df_add_same_position(df)

        #first columns in output file
        first_cols = ['ID', 'SeriesDescription', 'SliceThickness',
                       'likely_ncct',  'likely_cta', 'likely_ctp', 'likely_pwi', 'likely_dwi',
                      'nfiles', 'same_position_number', 'scandir',
                      'SelectedDateTime', 'DateTimeSelected',
                      'AcquisitionDateTime', 'AcquisitionDate', 'AcquisitionTime',
                      'ContentDateTime', 'ContentDate', 'ContentTime',
                      'SeriesDateTime', 'SeriesDate', 'SeriesTime',
                      ]
        df = df[[c for c in first_cols if c in df.columns] + [c for c in df.columns if c not in first_cols]]
        if redo_timestamps:
            df = pd_redo_timestamp(df)

        if redo_labelling:
            out = []
            for ID, tmp in tqdm(df.groupby('ID'), desc='Redoing labelling per ID'):
                tmp['ID'] = ID
                tmp['DateTimeSelected'] = tmp.apply(lambda row: row.get(row.get("datetimevar"), None), axis=1)
                tmp.sort_values(by=['DateTimeSelected'], inplace=True)
                tmp = dwi_identifier(tmp, n_same_pos=(2, 14))
                tmp = perf_identifier(tmp, n_same_pos=(14, 1e6))
                tmp = ncct_identifier(tmp)
                tmp = cta_identifier(tmp)
                out.append(tmp)
            df = pd.concat(out, ignore_index=True)
            #df.to_excel(f_out, index=False)
            #df.to_pickle(f_out.replace('.xlsx', '.pic'))

        df.to_pickle(f_out.replace('.xlsx', '.pic'))
        df.to_excel(f_out, index=False)
    else:
        df = pd.read_pickle(f_out.replace('.xlsx', '.pic'))
        df.index = df['ID']

    #labels set on baseline and followup timepoint
    print(f'Adding baseline and followup labels to combined metadata in \n{f_out}')
    f_timedata = os.path.join(os.path.dirname(f_out), 'LVO_labels.xlsx')
    timedata = pd.read_excel(f_timedata).drop_duplicates(subset='id', keep='first').set_index('id')
    xa_dct = pd.to_datetime(timedata[timedata['timepoint3_desc'] == 'first_xa']['timepoint3']).to_dict()
    bl_dct = (pd.to_datetime(timedata[timedata['timepoint3_desc'] != 'first_xa']['timepoint2']) + pd.Timedelta(
        hours=5)).to_dict()
    evt_dct = {**xa_dct, **bl_dct}
    out = []
    for ID, tmp in df.groupby('ID'):
        if ID in evt_dct:
            evt_time = evt_dct[ID]
            tmp['baseline'] = tmp['DateTimeSelected'] < evt_time
            tmp['followup'] = tmp['DateTimeSelected'] >= evt_time
            tmp['ID'] = ID
            out.append(tmp)
    df = pd.concat(out, ignore_index=True)

    print(f'Writing combined metadata to {f_out}\n', 'Length of combined metadata:', len(df))
    df.to_excel(f_out, index=False)
    df.to_pickle(f_out.replace('.xlsx', '.pic'))
    # else:
    #     #df = pd.read_excel(f_out)
    #     df = pd.read_pickle(f_out.replace('.xlsx', '.pic'))
    #     df.index = df['ID']

    print(f'Matching PWI to DWI and writing to {os.path.join(os.path.dirname(f_out), "matched_pwi_dwi.xlsx")}')
    f_matched_pwi_dwi = os.path.join(os.path.dirname(f_out), 'matched_pwi_dwi.xlsx')
    if not os.path.exists(f_matched_pwi_dwi):
        pwi_dwi = match_pwi_dwi(df)
        pwi_dwi.index = pwi_dwi['ID']
        pwi_dwi.to_excel(f_matched_pwi_dwi, index=False)
    else:
        pwi_dwi = pd.read_excel(f_matched_pwi_dwi, index_col='ID')

    f_dwiblfu = os.path.join(os.path.dirname(f_out), 'all_matched_dwi_blfu.xlsx')
    f_selected_blfu = os.path.join(os.path.dirname(f_out), 'selected_matched_dwi_blfu.xlsx')
    if not os.path.exists(f_dwiblfu):
        baseline_dwi = df[
            (df['likely_dwi'] != False) &
            (df['baseline'])
            ].copy()

        baseline_dwi = baseline_dwi.sort_values(['ID', 'likely_dwi'])

        letters = 'abcdefghijklmnopqrstuvwxyz'

        # Number of baseline DWIs per ID
        baseline_dwi['n'] = baseline_dwi.groupby('ID')['likely_dwi'].transform('size')

        # Letter suffix for IDs with multiple entries
        baseline_dwi['suffix'] = (
            baseline_dwi.groupby('ID')
            .cumcount()
            .map(lambda x: letters[x])
        )

        baseline_dwi['key'] = baseline_dwi.apply(
            lambda row: (
                str(row['ID']).replace('-','')
                if row['n'] == 1
                else f"{row['ID'].replace('-','')}-{row['suffix']}"
            ),
            axis=1
        )

        id2id = (
            baseline_dwi
            .groupby('ID')
            .apply(lambda x: dict(zip(x['likely_dwi'], x['key'])))
            .to_dict()
        )

        #make sure secondary label is available
        ID2 = []
        for id_, dwi in zip(df['ID'], df['likely_dwi']):
            if (id_ in id2id.keys()) and (dwi!=False):
                id2 = id2id[id_].get(dwi)
            else:
                id2 = None
            ID2.append(id2)
        df['org_ID'] = df['ID']
        df['ID'] = ID2

        baseline_dwi_dct = baseline_dwi.set_index('key')['likely_dwi'].to_dict()

        dwiblfu, selected_dwiblfu = match_dwi_blfu(df, baseline_dwi_dct, alternative_ID='org_ID')
        dwiblfu.to_excel(f_dwiblfu, index=False)
        selected_dwiblfu.to_excel(f_selected_blfu, index=False)

        # baseline_pwi_dwi_dct = pwi_dwi[(pwi_dwi['PWI'] == 'PWI_1') & (pwi_dwi['baseline_PWI'])]['DWI'].to_dict()
        # dwiblfu, selected_dwiblfu = match_dwi_blfu(df, baseline_pwi_dwi_dct)
        # dwiblfu.to_excel(f_dwiblfu.replace('.xlsx', '_w-pwi.xlsx'), index=False)
        # selected_dwiblfu.to_excel(f_selected_blfu.replace('.xlsx', '_w-pwi.xlsx'), index=False)

def match_pwi_dwi(df, extra_cols=None, datetimevars=('DateTimeSelected','AcquisitionDateTime', 'ContentDateTime', 'SeriesDateTime')):
    """
    Match each PWI to the closest DWI in time within each ID.

    Parameters
    ----------
    df : pd.DataFrame
    extra_cols : list[str], optional
        Columns from the original dataframe to include for both
        the matched PWI and DWI rows.

    Returns
    -------
    pd.DataFrame
    """
    if extra_cols is None:
        extra_cols = ['SeriesDescription', 'SliceThickness',
                      'baseline', 'followup', 'DateTimeSelected',
                      'nfiles', 'same_position_number', 'scandir', 'pid', 'dcmfile',
                      #'AcquisitionDateTime', 'AcquisitionDate', 'AcquisitionTime',
                      'ImageType', #'likely_pwi', 'likely_dwi',
                     'Modality', 'AccessionNumber', 'Manufacturer',
                     'StudyInstanceUID', 'SeriesInstanceUID', 'StudyID', 'SeriesNumber']
    matches = []

    for ID, subdf in tqdm(df.groupby('ID'), desc='Matching PWI to DWI'):

        pwi = subdf[subdf['likely_pwi'] != False].copy()
        dwi = subdf[subdf['likely_dwi'] != False].copy()

        if pwi.empty or dwi.empty:
            continue

        for dtv in datetimevars:
            if dtv in pwi.columns:
                pwi[dtv] = pd.to_datetime(pwi[dtv])
            if dtv in dwi.columns:
                dwi[dtv] = pd.to_datetime(dwi[dtv])

        for _, pwi_row in pwi.iterrows():

            for dtv in datetimevars:
                time_diffs = (
                    dwi[dtv]
                    - pwi_row[dtv]
                ).abs()
                if not all(pd.isna(v) for v in time_diffs):
                    break
            if all(pd.isna(v) for v in time_diffs):
                print(f"Warning: No valid datetime found for PWI ID {ID}. Skipping this PWI row.")
                continue

            idx = time_diffs.idxmin()
            dwi_row = dwi.loc[idx]

            match = {
                'ID': ID,
                'PWI': pwi_row['likely_pwi'],
                'PWI_time': pwi_row[dtv],
                'DWI': dwi_row['likely_dwi'],
                'DWI_time': dwi_row[dtv],
                'time_difference_minutes':
                    time_diffs.loc[idx].total_seconds() / 60,
            }

            for col in extra_cols:
                if col in pwi:
                    match[f'{col}_PWI'] = pwi_row[col]
                if col in dwi:
                    match[f'{col}_DWI'] = dwi_row[col]

            matches.append(match)
        # except Exception as e:
        #     print(f"Error matching PWI and DWI for ID {ID}: {e}")
        #     continue

    return pd.DataFrame(matches)


def match_dwi_blfu(
    df,
    reference_dict,
    extra_cols=None,
    alternative_ID='org_ID'
):
    if extra_cols is None:
        extra_cols = ['SeriesDescription', 'SliceThickness',
                      'nfiles', 'same_position_number', 'scandir', 'pid', 'dcmfile',
                      #'AcquisitionDateTime', 'AcquisitionDate', 'AcquisitionTime',
                      'ImageType', #'likely_pwi', 'likely_dwi',
                     'Modality', 'AccessionNumber', 'Manufacturer',
                     'StudyInstanceUID', 'SeriesInstanceUID', 'StudyID', 'SeriesNumber']


    rows = []

    #for ID, subdf in tqdm(df.groupby('ID'), desc='Matching DWI baseline and follow-up'):
    for ID, subdf in tqdm(df.groupby('ID'), desc='Matching DWI baseline and follow-up'):

        baseline_label = reference_dict.get(ID)
        if baseline_label is None:
            continue

        if alternative_ID is not None:
            ID2 = subdf[alternative_ID].iloc[0]
            subdf = df[df[alternative_ID] == ID2].copy()

        dwi = subdf[subdf['likely_dwi'] != False].copy()

        baseline = dwi[dwi['likely_dwi'] == baseline_label]

        if len(baseline) != 1:
            continue

        baseline = baseline.iloc[0]
        baseline_time = baseline['DateTimeSelected']

        dwi['hours_from_baseline'] = (
            dwi['DateTimeSelected'] - baseline_time
        ).dt.total_seconds() / 3600

        dwi = dwi[dwi['likely_dwi'] != baseline_label].copy()

        used = set()

        windows = {
            '8_30h': {
                'mask': dwi['hours_from_baseline'].between(8, 30),
                'target': 24,
                'preference':1
            },
            '4_72h': {
                'mask': dwi['hours_from_baseline'].between(4, 72),
                'target': 48,
                'preference': 2
            },
            '72_120h': {
                'mask': dwi['hours_from_baseline'].between(72, 120),
                'target': 72,
                'preference': 3
            }
        }

        for window_name, cfg in windows.items():

            candidates = dwi[cfg['mask']].copy()

            if len(candidates) == 0:
                continue

            candidates = candidates[
                ~candidates['likely_dwi'].isin(used)
            ]

            if len(candidates) == 0:
                continue

            candidates['distance_to_target'] = (
                candidates['hours_from_baseline'] - cfg['target']
            ).abs()

            followup = candidates.sort_values(
                'distance_to_target'
            ).iloc[0]

            used.add(followup['likely_dwi'])

            row = {
                'ID': ID,
                'window': window_name,

                'baseline_dwi': baseline['likely_dwi'],
                'baseline_time': baseline_time,

                'followup_dwi': followup['likely_dwi'],
                'followup_time': followup['DateTimeSelected'],

                'hours_from_baseline':
                    followup['hours_from_baseline'],

                'preference': cfg['preference']
                #'duplicate_ID': baseline['ID2']
            }

            for col in extra_cols:
                row[f'{col}_baseline'] = baseline[col]
                row[f'{col}_followup'] = followup[col]

            rows.append(row)
    dwiblfu = pd.DataFrame(rows)

    selected_dwiblfu = (
        dwiblfu.sort_values('preference')
        .groupby('ID', as_index=False)
        .first()
    )
    return dwiblfu, selected_dwiblfu

if __name__ == "__main__":
    args = get_general_args()

    get_full_combined(args.output, redo_timestamps=True, redo_labelling=True)

    ##get_full_combined(args.output, redo_timestamps=True, redo_labelling=True)
    for batch in ['batch1', 'batch2', 'batch_2nd_Encounter', 'batch3', 'batch4', 'batch5', 'batch6', 'batch7',
                  'batch8']:
        batch_dir = os.path.join(args.input, batch)
        if not os.path.exists(batch_dir):
            continue
        print(f'--------- Processing {batch_dir} ---------')
        if args.njobs==1:
            get_all_metadata(batch_dir, args.output, file_limits=(5, 1e6), multipos_limits=(0, 1e6), skip_tags=['Privatetagdata'], export_to='.xlsx')
        else:
            jobs = chunk_jobs(args.input, args.output, jobs=args.njobs, file_limits=(5,1e6), multipos_limits=(0, 1e6), skip_tags=['Privatetagdata'], export_to='.xlsx')
            with Pool(processes=args.njobs) as pool:
                pool.starmap(get_all_metadata, jobs)

    get_full_combined(args.output, redo_timestamps=True, redo_labelling=True)
