
import os
import pydicom
import pandas as pd
from dicomdetector.metadata import get_tag_value

# Function used for CTP/PWI/DWI/ASL identification
def check_same_position(files, extract_time=True):
    """
    Checks if and how many dcm files there are
    with the same position. If this is >20 it
    is very likely a CTP and not a multi phase CTA
    """

    # define a reference file to check
    d1 = pydicom.dcmread(files[10].open(), stop_before_pixels=True)
    # try to find the position tag
    try:
        position_tag = (0x0020, 0x0032)
        position = d1[position_tag].value
        found = True
    except:
        try:
            position_tag = 'ImagePositionPatient'
            position = d1[position_tag].value
            found = True
        except:
            found = False

    if found:
        # iterate over all files and store the ones with the same position
        same_position_files, timevars = [], []
        for i in range(len(files)):
            d = pydicom.dcmread(files[i].open(), stop_before_pixels=True)
            if d[(0x0020, 0x0032)].value == position:
                same_position_files.append(files[i])

    return same_position_files

def n_same_position_from_dicom(dcm_dir, position_tag=((0x0020, 0x0032),'ImageOrientation(Patient)'), fix=10):
    """
    Checks if there are multiple timeframes in the same position
    in a dicom folder. This is used to find CTP scans
    """
    file10 = os.path.join(dcm_dir, os.listdir(dcm_dir)[fix])

    dcm = pydicom.dcmread(file10, stop_before_pixels=True)
    pos10 = get_tag_value(dcm, *position_tag)

    same_position = []
    for f in os.listdir(dcm_dir):
        file = os.path.join(dcm_dir, f)
        dcm = pydicom.dcmread(file, stop_before_pixels=True)
        pos = get_tag_value(dcm, *position_tag)
        if pos == pos10:
            same_position.append(pos)

    return len(same_position)

