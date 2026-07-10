import ast
import os
import sys
import pandas as pd
import numpy as np
import ast

#import lists of kernels for inclusion
from default_information import CTA_kernels, NCCT_kernels, NCCT_BONE_kernels, \
    DE_kernels, Topogram_kernel, Testbolus_kernel, multi_modal_kernels
#import descriptions for inclusion
from default_information import CTA_description, NCCT_description, NCCT_BONE_description, \
    DE_description, DSA_description, CTP_description, DWI_description_excl, PERF_description_excl
#import exclusion descriptions
from default_information import EXCLUSION_description
from utils import get_general_args

def map_imagetype(cell):
    s = str(cell).lower()
    if 'second' in s:
        return 2
    elif 'deriv' in s:
        return 3
    elif 'prima' in s or 'orig' in s:
        return 1
    else:
        return 4 # "any other number for rest" - adjust as needed
def dwi_identifier(mdata, n_same_pos=(2,12), sd_excl=[ *EXCLUSION_description, *DWI_description_excl]):

    if isinstance(mdata, pd.Series):
        mdata = mdata.to_frame().T

    likely_dwi = []
    i = 1
    for __, row in mdata.iterrows():
        try:
            if row['Modality']!='MR':
                likely_dwi.append(False)
            elif any([sde.lower() in row['SeriesDescription'].lower() for sde in sd_excl]):
                likely_dwi.append(False)
            elif row['same_position_number'] < n_same_pos[0] or row['same_position_number'] > n_same_pos[1]:
                likely_dwi.append(False)
            else:
                likely_dwi.append(f'DWI_{i}')
                i+=1
        except:
            likely_dwi.append(False)
    mdata['likely_dwi'] = likely_dwi
    return mdata

def perf_identifier(mdata, n_same_pos=(12,1e6), sd_excl=['asl', 'fmri', 'qsm',*EXCLUSION_description, PERF_description_excl]):

    if isinstance(mdata, pd.Series):
        mdata = mdata.to_frame().T

    likely_ctp, likely_pwi = [], []
    i_ctp, i_pwi = 1, 1
    for __, row in mdata.iterrows():
        try:
            #exclusion based on lack of multiple frames with same position
            if row['same_position_number'] < n_same_pos[0] or row['same_position_number'] > n_same_pos[1]:
                likely_ctp.append(False)
                likely_pwi.append(False)
                continue

            #exclusion based on description
            if any([sde.lower() in row['SeriesDescription'].lower() for sde in sd_excl]):
                likely_ctp.append(False)
                likely_pwi.append(False)
                continue

            if row['Modality']=='CT':
                likely_ctp.append(f'CTP_{i_ctp}')
                likely_pwi.append(False)
                i_ctp+=1
            elif row['Modality']=='MR':
                likely_ctp.append(False)
                likely_pwi.append(f'PWI_{i_pwi}')
                i_pwi+=1
        except:
            likely_ctp.append(False)
            likely_pwi.append(False)

    mdata['likely_ctp'] = likely_ctp
    mdata['likely_pwi'] = likely_pwi

    return mdata

def cta_identifier(mdata,
                   min_files = 80,
                   incl_descr=[*CTA_description],
                   excl_description=[*EXCLUSION_description, *CTP_description, *NCCT_BONE_description, *DE_description],
                   select_kernels=[*CTA_kernels],
                   mm_kernels = [*multi_modal_kernels],
                   excl_kernels = [*Topogram_kernel, *Testbolus_kernel, *NCCT_BONE_kernels, *NCCT_kernels],
                   ):
    """
    Identifies CTA from metatdata dataframe following steps:
    Sort thinnest slices first
    1: Exclude folders with <min_files
    2: Exclude excl_description cases
    3: Check if modality is CT, if not exclude
    4: Check if ConvolutionKernel is in select_kernels if yes include as CTA
    5: Check if ConvolutionKernel is in mm_kernels if yes check description to label as CTA
    6: Check if ConvolutionKernel is in excl_kernels list to exclude
    7: Use description for inclusion as last resort
    """


    if isinstance(mdata, pd.Series):
        mdata = mdata.to_frame().T

    if 'ImageType' in mdata.columns:
        #number order: primary/original, secondary/derived, processed, other
        mdata['ImageTypeNumber'] = mdata['ImageType'].apply(map_imagetype)
    else:
        mdata['ImageTypeNumber'] = 4

    if 'SliceThickness' in mdata.columns:
        mdata.sort_values(by=['SliceThickness','ImageTypeNumber'], ascending=[True,True], inplace=True)

    likely_cta = []
    i = 1
    for __, row in mdata.iterrows():
        use_description = False
        try:
            if row.get("nfiles", min_files+100)<min_files:
                likely_cta.append(False)
                continue

            if row.get('same_position_number', 0) > 1:
                likely_cta.append(False)
                continue

            #filter out exclusion descriptions
            SeriesDescription = row.get('SeriesDescription', '')
            if any([sde.lower() in SeriesDescription.lower() for sde in excl_description]):
                likely_cta.append(False)
                continue

            #if modality is MR also continue
            if 'Modality' in row.index:
                if row['Modality']!='CT':
                    likely_cta.append(False)
                    continue

            ck = row['ConvolutionKernel']
            if isinstance(ck, float):
                if np.isnan(ck):
                    if any([incl.lower() in SeriesDescription.lower() for incl in incl_descr]):
                        likely_cta.append(f'CTA_{i}')
                        i += 1
                    else:
                        likely_cta.append(False)
                    continue
                else:
                    ck = str(ck)

            if isinstance(ck, list) or isinstance(ck, tuple):
                ck = ''.join(ck)
                print('ConvolutionKernel is list or tuple, joining to string')

            if isinstance(ck, str):
                if '[' in ck or '(' in ck:
                    ck = ''.join(ast.literal_eval(ck))

                if any([select_ck.lower() in ck.lower() for select_ck in select_kernels]):
                    likely_cta.append(f'CTA_{i}')
                    i+=1
                elif any([mm_ck.lower() in ck.lower() for mm_ck in mm_kernels]):
                    if any([incl.lower() in SeriesDescription.lower() for incl in incl_descr]):
                        likely_cta.append(f'CTA_{i}')
                        i+=1
                    else:
                        likely_cta.append(False)
                elif any([exck.lower() in ck.lower() for exck in excl_kernels]):
                    likely_cta.append(False)
                else:
                    if any([incl.lower() in SeriesDescription.lower() for incl in incl_descr]):
                        likely_cta.append(f'CTA_{i}')
                        i += 1
                    else:
                        likely_cta.append(False)
            else:
                if any([incl.lower() in SeriesDescription.lower() for incl in incl_descr]):
                    likely_cta.append(f'CTA_{i}')
                    i += 1
                else:
                    likely_cta.append(False)
        except Exception as e:
            likely_cta.append(False)
    mdata['likely_cta'] = likely_cta
    return mdata


def ncct_identifier(mdata,
                    min_files=10,
                    incl_descr=[*NCCT_description],
                    excl_description=['iodine', *EXCLUSION_description, *CTP_description, *NCCT_BONE_description, *CTA_description, *DE_description],
                    select_kernels=[*NCCT_kernels],
                    mm_kernels=[*multi_modal_kernels],
                    excl_kernels=[*Topogram_kernel, *Testbolus_kernel, *NCCT_BONE_kernels, *CTA_kernels],
                    ):
    """
    Identifies NCCT from metatdata dataframe following steps:
    Sort thinnest slices first
    1: Exclude folders with <min_files
    2: Exclude excl_description cases
    3: Check if modality is CT, if not exclude
    4: Check if ConvolutionKernel is in select_kernels if yes include as NCCT
    5: Check if ConvolutionKernel is in mm_kernels if yes check description to label as NCCT
    6: Check if ConvolutionKernel is in excl_kernels list to exclude
    7: Use description for inclusion as last resort
    """

    if isinstance(mdata, pd.Series):
        mdata = mdata.to_frame().T

    if 'ImageType' in mdata.columns:
        #number order: primary/original, secondary/derived, processed, other
        mdata['ImageTypeNumber'] = mdata['ImageType'].apply(map_imagetype)
    else:
        mdata['ImageTypeNumber'] = 4

    if 'SliceThickness' in mdata.columns:
        mdata.sort_values(by=['SliceThickness','ImageTypeNumber'], ascending=[False,True], inplace=True)

    likely_ncct = []
    i = 1
    for __, row in mdata.iterrows():
        try:
            if row.get("nfiles", min_files + 100) < min_files:
                likely_ncct.append(False)
                continue

            if row.get('same_position_number', 0) > 1:
                likely_ncct.append(False)
                continue

            # filter out exclusion descriptions
            SeriesDescription = row.get('SeriesDescription', '')
            if any([sde.lower() in SeriesDescription.lower() for sde in excl_description]):
                likely_ncct.append(False)
                continue

            # if modality is MR also continue
            if 'Modality' in row.index:
                if row['Modality'] != 'CT':
                    likely_ncct.append(False)
                    continue

            ck = row['ConvolutionKernel']
            if isinstance(ck, float):
                if np.isnan(ck):
                    if np.isnan(ck):
                        if any([incl.lower() in SeriesDescription.lower() for incl in incl_descr]):
                            likely_ncct.append(f'NCCT_{i}')
                            i += 1
                        else:
                            likely_ncct.append(False)
                        continue
                else:
                    ck = str(ck)

            if isinstance(ck, list) or isinstance(ck, tuple):
                ck = ''.join(ck)
                print('ConvolutionKernel is list or tuple, joining to string')

            if isinstance(ck, str):
                if '[' in ck or '(' in ck:
                    ck = ''.join(ast.literal_eval(ck))

                if any([select_ck.lower() in ck.lower() for select_ck in select_kernels]):
                    likely_ncct.append(f'NCCT_{i}')
                    i += 1
                elif any([mm_ck.lower() in ck.lower() for mm_ck in mm_kernels]):
                    if any([incl.lower() in SeriesDescription.lower() for incl in incl_descr]):
                        likely_ncct.append(f'NCCT_{i}')
                        i += 1
                    else:
                        likely_ncct.append(False)
                elif any([exck.lower() in ck.lower() for exck in excl_kernels]):
                    likely_ncct.append(False)
                else:
                    if any([incl.lower() in SeriesDescription.lower() for incl in incl_descr]):
                        likely_ncct.append(f'NCCT_{i}')
                        i += 1
                    else:
                        likely_ncct.append(False)
            else:
                if any([incl.lower() in SeriesDescription.lower() for incl in incl_descr]):
                    likely_ncct.append(f'NCCT_{i}')
                    i += 1
                else:
                    likely_ncct.append(False)

        except Exception as e:
            likely_ncct.append(False)
    mdata['likely_ncct'] = likely_ncct
    return mdata

if __name__ == "__main__":
    args = get_general_args()

    print(1)
