import os
from multiprocessing import Pool
from utils import get_general_args
from get_metadata import get_all_metadata, get_full_combined, chunk_jobs

if __name__ == "__main__":
    args = get_general_args()

    print(f'--------- Processing {args.input} ---------')
    if args.njobs==1:
        #sequential processing of IDs
        get_all_metadata(args.input, args.output, file_limits=(5, 1e6), multipos_limits=(0, 1e6), skip_tags=['Privatetagdata'], export_to='.xlsx')
    else:
        #chunk IDs for processing
        jobs = chunk_jobs(args.input, args.output, jobs=args.njobs, file_limits=(5,1e6), multipos_limits=(0, 1e6), skip_tags=['Privatetagdata'], export_to='.xlsx')
        with Pool(processes=args.njobs) as pool:
            pool.starmap(get_all_metadata, jobs)

    #Acquired one single excel file
    get_full_combined(args.output, redo_timestamps=True, redo_labelling=True)
