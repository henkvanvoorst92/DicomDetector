
#Inclusion kernels for various modalities
CTA_kernels = [ 'B26f' ,'B31f', 'B40f', 'B46f', 'Br38f2', 'Br40d3', 'Bv36d3', 'Bv38f2', 'Bv40d3',
            'Bv40f3', 'Bv44d1', 'Bv49d3', 'Bv49f3', 'DETAIL', 'FC05', 'H20s',
            'Hr40d3', 'Hr49d3', 'Hv38f3', 'Hv40f3', 'Hv40f4', 'I26f2', 'I26f3', 'I26f4',
            'I30f2', 'I30f4', 'I40f2', 'I31f2', 'I31f3', 'I40f3', 'I46f', 'I46f1', 'I46f3',
            'IMR1,Routine', 'IMR1,Soft Tissue', 'YC', 'I70f', 'IMR2,Routine',
            'J30f2', 'Hr38d4', 'Hv40s3', 'Hv40s', 'I26f', 'Br38f3', 'BRAIN_CTA', 'FC03', 'FC05', 'FC02', 'FC08',
            'FC41', 'STANDARD2', 'YC', 'H10f', 'D30f', 'DETAIL', 'BODY_SHARP', 'Br36s', 'H40f', 'FC43', ]

NCCT_kernels = ['FC21', 'FC68', 'H31f', 'H31s', 'H40s', 'H41s',
             'Hf38s', 'Hf38s3', 'Hr38s3', 'Hr40f3', 'Hr40s', 'Hr40s3',
             'J30s2', 'J30s4', 'J40f4', 'J40s2', 'J40s3', 'J40s5', 'J45s4',
             'SOFT', 'SOFT#', 'UB',
             'Br36s2', 'Br36s3', 'BRAIN_LCD', 'FC21', 'FC26', 'FC63', 'FC64', 'FC68', 'UC', 'H41f',
             'Hf35s', 'Hr38s']

NCCT_BONE_kernels = ['H60f', 'Hr56f', 'Hr56s3', 'Hr64h1', 'Hr64h2', 'Hr68h', 'J37f3', 'J70h1', 'J70h2', 'J70h3',
                  'H60f', 'Hr56f', 'Hr64h1', 'Hr68h', 'J70h1', 'J70h3', 'FC30', 'FC35', 'YA', 'Hr60f3',
                  'Hr64h', 'BONE', 'BONEPLUS', 'H70h', 'H60s', 'Hr68h3', 'Hr69h3', 'YB', ]  #

DE_kernels = ['Q30f3', 'Q33f3', 'Q34s3', 'Q40f3', 'Qr40f2', 'Qr40f3', 'Hr38d3', 'Qr40d3', 'Hr36s3', 'Hr38f3',
           'J45f2', 'J45f3', 'D26f', 'D34f', 'Q34f3', 'Q40s3', 'Qr32s2', 'Qr40s2', 'Qr40s3', ]

Topogram_kernel = ['FL03', 'FL04', 'T20f', 'Tr20f']
Testbolus_kernel = ['B30f', 'Br36f', 'D20f', 'B30s', 'B31s']

# kernel descriptions for kernels with multiple modalities
multi_modal_kernels = ['STANDARD', 'H30f', 'J30f4', 'J40f3', 'B', 'IMR1,Brain Routi', 'Hr38s3',
                       'J30s3', ]

#Description exclusion strings
EXCLUSION_description = ['cor', 'sag', 'pjn', 'overlay', 'mip', 'rendering']

#Description inclusion string
cardio_description = ['cardio', 'cardiac seq']
DE_description = ['de_he', 'mixed', 'de car', 'de_car', 'de hem', 'hem_de', 'de_sche',
                           'de post-coiling', '140kv', '80kv', 'de cer', 'de_iat', 'de cer', 'de_brain',
                           'de_small', 'iodine']
CTA_description = ['mip', 'cta', 'art', 'carotid', 'angio', 'willis', 'missing', 'cerebrum 0.75 j30f 4', 'delay',
                   'vaten', 'thin slices', 'cvw', 'ax 1', 'cow', 'mpr 1', 'cerebrum 2.0 mpr',
                   'cerebrum 0.75  h30f', 'sag 2 incr 1', 'cor 2 incr 1', 'cta hersenen', 'carotis',
                   'cerebrum 0.75  j30f  4', 'cerebrum 5.0  j30f  4', 'hersenen cor 1', 'hersenen sag 1',
                   'mpr cor 1-1', 'mpr sag 1-1', 'hals', 'imr ax hersenen', 'TI-CTA', 'headangio',
                   'cerebrum col 0', 'cerebrum col  1', 'cerebrum col 1']
NCCT_description = ['zonder contrast', 'blanco', '11912593', 'schedel', 'cerebrum', '_hem', 'mpr tra F_0.4',
                    'hemorrhage', 'hersenen', 'sbi', 'mpr cor', 'mpr tra', 'mpr sag', 'mpr 5', 'zc sched',
                    'cerebr spi', 'mpr cer spi', 'brein b', 'vnc 5', 'ce 5']
CTP_description = ['perfusie', 'perfusion', 'ctp', 'smart prep', 'perf', '5 AX, iDose (3)', 'vpct']
DSA_description = ['strokebehandeling', 'cerebral', 'lao', 'carotis', 'bronchialis', '4f', 'fluor', 'vfr',
                   'fps']
DWI_description_excl = ['asl', 'fmri', 'qsm', 'cor', 'sag', 'pjn', 'perf', 'cine', 'ivim', 'dti', 'pwi', 'swi']
PERF_description_excl = ['asl', 'fmri', 'qsm', 'cor', 'sag', 'pjn', 'cine', 'ivim', 'dti', 'swi']

DE_description = ['dual', 'overlay']
Testbolus_description = ['tracker', 'smart prep', 'testbolus', 'monitoring  10']

NCCT_multimodal = ['ax hers imr', 'ax 4mm', 'imr 0,8/0,4', 'imr 0.9/0.45', 'imr tra',
                   'ts_bl_imr1br', 'ax 3', 'cor 4mm', 'cor 3', 'mpr  cor  f_0.4',
                   'sag 4', 'sag 3', 'sag 2', 'mpr sag']
CTA_multimodal = ['ax imr', 'contrast', 'imr ax', 'axi 1-1', 'gehele traject', 'ax',
                  '+c imr 0.8/0.4', 'car', 'cor 1', 'cor 2 om 1', 'cor 1-1', 'cta',
                  'sag 1']
non_stroke_descr = ['long', 'onco ', 'thorax', 'zc thabd trauma', 'SBI(C_SC_PE_N_B_U)', 'aangezicht',
                    'schouder', 'abd.', 'abdomen']
three_D_descr = ['3d']
NCCT_BONE_description = ['cta schedel  3.0  i70f', 'bone']

####

CTA_short = ['A', 'C', ]

NCCT_BONE_SHORT = ['D']

CTP_list = ['H20f', 'Hr35f', 'Hr36d', 'Hr36f', 'UA', 'Hf35f']
DSA_list = ['HUNormal']
CWK_list = ['Hr69d3', 'I70h2', 'I70h2', 'Br60f3', 'Br62f3']
non_stroke_list = ['I70f3', 'B60f', 'Br40f3', 'FC19', 'FC86']

LowDose_list = ['FC07', ]
CTA_or_DE_list = ['I30f3', ]
RAPID_software_list = ['rapid']
rgb_maps_list = ['rgb']

virtual_non_contrast_list = ['vnc']