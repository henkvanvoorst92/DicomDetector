# DicomDetector

This repository automatically iterates over all DICOM folders in a repository and extracts DICOM tag metadata. The metadata is stored in Excel files for review. Based on the metadata in these Excel files, automated labels are created for several imaging modalities:

* NCCT
* CTA
* CTP
* DWI
* PWI

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

## Usage

1. Place your DICOM folders in the repository structure. The root of your input data should contain subdirectories which are unique IDs.
2. Run the metadata extraction workflow: see main.py or run.sh.
3. Review the generated Excel files.
4. Use the modality labels and `likely_modality` output for downstream analysis.
