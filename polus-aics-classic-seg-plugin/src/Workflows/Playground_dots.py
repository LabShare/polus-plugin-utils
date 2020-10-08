import numpy as np
import cv2
import os
import logging, sys
import traceback
import javabridge as jutil
import bioformats
from bfio import BioReader, BioWriter
from pathlib import Path
from aicsimageio import AICSImage
from aicssegmentation.core.seg_dot import dot_3d, dot_3d_wrapper 
from aicssegmentation.core.pre_processing_utils import intensity_normalization, image_smoothing_gaussian_slice_by_slice, image_smoothing_gaussian_3d
from skimage.morphology import remove_small_objects, watershed, dilation, erosion, ball
from skimage.feature import peak_local_max
from skimage.measure import label
from scipy.ndimage import distance_transform_edt


def segment_images(inpDir, outDir, config_data):  

    logging.basicConfig(format='%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S')
    logger = logging.getLogger("main")
    logger.setLevel(logging.INFO)

    try : 
        logger.info('Initializing the javabridge...')
        log_config = Path(__file__).parent.parent.joinpath("log4j.properties")
        jutil.start_vm(args=["-Dlog4j.configuration=file:{}".format(str(log_config.absolute()))],class_path=bioformats.JARS)

        inpDir_files = os.listdir(inpDir)
        for i,f in enumerate(inpDir_files):
            logger.info('Segmenting image : {}'.format(f))
            
            # Load an image
            br = BioReader(os.path.join(inpDir,f))
            image = br.read_image()
            structure_channel = 0 
            struct_img0 = image[:,:,:,structure_channel,0]
            struct_img0 = struct_img0.transpose(2,0,1).astype(np.float32)

            # main algorithm
            intensity_scaling_param = config_data['intensity_scaling_param']
            struct_img = intensity_normalization(struct_img0, scaling_param=intensity_scaling_param)
                
            gaussian_smoothing_sigma = config_data['gaussian_smoothing_sigma'] 
            if config_data["gaussian_smoothing"] == "gaussian_slice_by_slice":
                structure_img_smooth = image_smoothing_gaussian_slice_by_slice(struct_img, sigma=gaussian_smoothing_sigma)
            else:
                structure_img_smooth = image_smoothing_gaussian_3d(struct_img, sigma=gaussian_smoothing_sigma)    
            s3_param = config_data['s3_param']
            bw = dot_3d_wrapper(structure_img_smooth, s3_param)
            minArea = config_data['minArea']
            Mask = remove_small_objects(bw>0, min_size=minArea, connectivity=1, in_place=False) 
            Seed = dilation(peak_local_max(struct_img,labels=label(Mask), min_distance=2, indices=False), selem=ball(1))
            Watershed_Map = -1*distance_transform_edt(bw)
            seg = watershed(Watershed_Map, label(Seed), mask=Mask, watershed_line=True)
            seg = remove_small_objects(seg>0, min_size=minArea, connectivity=1, in_place=False)
            seg = seg >0
            out_img=seg.astype(np.uint8)
            out_img[out_img>0]=255

            # create output image
            out_img = out_img.transpose(1,2,0)
            out_img = out_img.reshape((out_img.shape[0], out_img.shape[1], out_img.shape[2], 1, 1))

            # write image using BFIO
            bw = BioWriter(os.path.join(outDir,f))
            bw.num_x(out_img.shape[1])
            bw.num_y(out_img.shape[0])
            bw.num_z(out_img.shape[2])
            bw.num_c(out_img.shape[3])
            bw.num_t(out_img.shape[4])
            bw.pixel_type(dtype='uint8')
            bw.write_image(out_img)
            bw.close_image()
             
    except Exception:
        traceback.print_exc()

    finally:
        # Close the javabridge regardless of successful completion
        logger.info('Closing the javabridge')
        jutil.kill_vm()
        
        # Exit the program
        sys.exit()        