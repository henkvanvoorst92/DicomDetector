# DicomDetector

This repository automatically iterates over all DICOM folders in a repository and extracts DICOM tag metadata. The metadata is stored in Excel files for review. Based on the metadata in these Excel files, automated labels are created for several imaging modalities:

* Noncontrast CT (NCCT): Selection relies on the DICOM tags `Convolution Kernel` and `Series description`
* CT angiography (CTA): Selection relies on the DICOM tags `Convolution Kernel` and `Series description`
* CT perfusion (CTP): Selection relies on the number (default>12) of DICOMs with the same `Image Position Patient` and secondary filtering for `Modality` and  `Series description`
* Perfusion weighted imaging (PWI) MR: Selection relies on the number (default>12) of DICOMs with the same `Image Position Patient` and secondary filtering for `Modality` and  `Series description`
* Diffusion Weighted Imaging (DWI): Selection relies on the number (default: 2-11) of DICOMs with the same `Image Position Patient` and secondary filtering for `Modality` and  `Series description`

For each modality, a `likely_modality` column is generated. This column contains `False` for excluded cases, or a `modality_number` ordered by preference of images and time tags.

Time tags are automatically adjusted when needed, with preference given to:

`AcquisitionDateTime` > `ContentDateTime` > `SeriesDatetime`

The current workflows are targeted toward image analysis of stroke patients and focus mainly on MR and CT modalities.

## Setup

1. Clone the repository.
2. Create a Python 3.11 environment.
3. Install the requirements:

```bash
pip install -r requirements.txt
```

## Usage Instructions

1. Place your DICOM folders in the repository structure. The root of your input data should contain subdirectories that are unique IDs.
   Structure:
   - `args.input`
     - ID1
     - ID2
     - IDx
2. Define an output folder `args.output`, in this folder, each ID will have an Excel file with all metadata.
3. Run the metadata extraction workflow (see main.py or run.sh.). `njobs` can be used for parallel processing.
   ```bash
    python main.py --input /pat/to/input/dir --output /path/to/output/dir --njobs 1
    ```
4. Review the generated Excel files.
5. Use the modality labels and `likely_modality` output for downstream analysis.
