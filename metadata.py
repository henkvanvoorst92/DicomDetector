import pandas as pd
import pydicom
import re
from datetime import datetime
import numpy as np
import os

def tags_of_all_dicoms_in_dir(p_dcmdir, mdct=None, stringconvert=False):
    out = []
    for f in os.listdir(p_dcmdir):
        file = os.path.join(p_dcmdir, f)
        dcm = pydicom.dcmread(file, stop_before_pixels=True)
        data = all_tag_values(dcm, mdct=mdct, stringconvert=stringconvert)
        out.append(data)

    mdct = create_mdct(dcm)
    out = pd.DataFrame(out, columns=list(mdct.keys()))

    return out


def detailed_tags_of_all_dicoms_in_dir(p_dcmdir, stringconvert=False):
    out = []
    for f in os.listdir(p_dcmdir):
        file = os.path.join(p_dcmdir, f)
        dcm = pydicom.dcmread(file, stop_before_pixels=True)
        mdct = create_mdct(dcm)
        data = all_tag_values(dcm, mdct=mdct, stringconvert=stringconvert)
        tmp = pd.DataFrame(data, index=list(mdct.keys())).T
        tmp['n_cols'] = len(tmp.columns)
        out.append(tmp)

    out = pd.concat(out)
    return out


def all_tag_values(dcm, mdct=None, stringconvert=False):
    # returns a set of dicom tags stripped from dcm (a dicom file)
    # mdct is a dictionary with
    # keys = dicom tag number (example: (0x0020, 0x0032))
    # values = corresponding dicom tag name ('ImagePositionPatient')
    # stringconvert is optional and converts all tags to strings
    out = []
    if mdct is None:
        mdct = create_mdct(dcm)

    for k, v in mdct.items():
        tag = get_tag_value(dcm, k, v)
        if stringconvert:
            tag = str(tag)
        out.append(tag)
    return out

def create_mdct(dcm):
    # extracts all metadata names and IDs
    mdct = {}
    # iterating over items does not work for v
    for k in dcm.keys():
        try:
            n = re.subn('[ ]()', '', str(dcm[k].name))[0]
            if n == 'PixelData':
                continue
            mdct[n] = k
        except:
            print('Does not work:', dcm[k])
    return mdct

def get_tag_value(dcm, tagno, tagname):
    """
    Returns the dicom tag value based on e a string name (tagname)
    or number (tagno: (0x0001,0x0001))
    """
    try:
        out = dcm[tagno].value
    except:
        try:
            out = dcm[tagname].value
        except:
            out = np.NaN
    return out


## function to extract all dicom tags
def get_tagnos_tagnames(dcm):
    """
    Returns lists of tag numbers and names from dicom
    tagno example: (0x0001,0x0001)
    """
    tagnos = list(dcm.keys())
    name2no = {}
    no2name = {}
    for tagno in tagnos:
        tagname = str(dcm[tagno].name)
        tagname = tagname.replace(' ', '')
        name2no[tagname] = tagno
        no2name[tagno] = tagname
    return name2no, no2name


def try_t_str(datestring:str, t_str:list=None):
    """
    Try different string formats provided in t_str (list)
    for a given datestring, returns the most appropriate found
    Warning!: the order of t_str is important, if a str in t_str
    fits the datastring the remaining t_str is not considered
    """
    if t_str is None:
        t_str= ["%Y%m%d%H%M%S", "%Y%m%d%H%M%S.%f",  # datetimeformats
                   "%d%m%Y%H%M%S", "%d%m%Y%H%M%S.%f",  # datetimeformats
                   "%m%d%Y%H%M%S.%f" "%m%d%Y%H%M%S",  # datetimeformats
                   "%Y%m%d", "%d%m%Y", "%m%d%Y",  # date formats
                   "%H%M%S", "%H%M%S.%f",  # time formats
                   ]



    for ts in t_str:
        try:
            out = datetime.strptime(datestring, ts)
            break
        except:
            out = np.NaN
            continue
    return out


# strip all dicom tags you can find in a single CTP frame
def complete_tag_values(dcm, stringconvert=False, skip_tags=[]):
    # return a list of key and values from Thosiba dicom tags
    # first extract the easy to access global tags
    tagname2no, tagno2name = get_tagnos_tagnames(dcm)
    if len(skip_tags) > 0:
        tagno2name = {k: v for k, v in tagno2name.items() if v not in skip_tags and k not in skip_tags}
        tagname2no = {k: v for k, v in tagname2no.items() if v not in skip_tags and k not in skip_tags}

    row_tags = all_tag_values(dcm, tagno2name, stringconvert=stringconvert)
    cols = list(tagno2name.values())

    # now extract the PerFrameFunctionalGroupsSequence and SharedFunctionalGroupsSequence tags
    # see also: https://stackoverflow.com/questions/74776837/pydicom-returns-keyerror-even-though-field-exists
    dcm_keys = list(dcm.keys())
    dcm_valnames = [v.name.replace(' ','') for v in dcm.values()]

    if 'PerFrameFunctionalGroupsSequence' in dcm_keys or 'PerFrameFunctionalGroupsSequence' in dcm_valnames:
        subdcm = dcm['PerFrameFunctionalGroupsSequence'][10]
        for subkey in subdcm.keys():
            try:
                if len(subdcm[subkey].value) == 0:
                    continue
                subsubdcm = subdcm[subkey][0]
                tagname2no, tagno2name = get_tagnos_tagnames(subsubdcm)
                r = all_tag_values(subsubdcm, tagno2name, stringconvert=True)
                row_tags.extend(r)
                cols.extend([f'PerFrameFunctionalGroupsSequence_{k}' for k in tagname2no.keys()])
            except Exception as e:
                print('Error in PerFrameFunctionalGroupsSequence:', e)

    if 'SharedFunctionalGroupsSequence' in dcm_keys or 'SharedFunctionalGroupsSequence' in dcm_valnames:
        subdcm = dcm['SharedFunctionalGroupsSequence'][0]
        for subkey in subdcm.keys():
            try:
                if len(subdcm[subkey].value) == 0:
                    continue
                subsubdcm = subdcm[subkey][0]
                tagname2no, tagno2name = get_tagnos_tagnames(subsubdcm)
                r = all_tag_values(subsubdcm, tagno2name, stringconvert=True)
                row_tags.extend(r)
                cols.extend([f'SharedFunctionalGroupsSequence_{k}' for k in tagname2no.keys()])
            except Exception as e:
                print('Error in SharedFunctionalGroupsSequence:', e)
    try:
        row_tags = np.asarray(row_tags, dtype=object)
        cols = np.array(cols, dtype=object)

        isna_vec = np.vectorize(pd.isna)
        na_mask = isna_vec(row_tags)

        row_tags = row_tags[~na_mask]
        cols = cols[~na_mask]
        output = pd.DataFrame(index=row_tags).reset_index().T
        output.columns = cols
    except:
        output = pd.DataFrame(index=row_tags).reset_index().T
        output.columns = cols

    return output