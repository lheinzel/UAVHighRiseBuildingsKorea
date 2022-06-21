import os
import numpy as np
import pandas as pd
from PIL import Image



def createLabelCSVForCroppedImage(sourceFile, sourceImage, targetDir, emptyDir, localPicSize, stride, minLblOverlap, label):
  #read-in csv-file with labels from original picture
  labels = pd.read_csv(sourceFile, delimiter = ';')

  #read-in original image 
  im_png = Image.open(sourceImage)
  im_as_array = np.array(im_png)

  #---------------------------------------------------
  ## calculate shapes

  #get x and y dimention of image: [x,y]
  glb_pic_size = im_as_array.shape[1::-1]

  # calculate number of elements
  nbr_of_elements_x = int((glb_pic_size[0] - localPicSize[0])/stride) + 1
  nbr_of_elements_y = int((glb_pic_size[1] - localPicSize[1])/stride) + 1

  # take edge stride in consideration (if local stride >= stride/2 than change stride for last picture, else throw rest)
  bool_x_stride = False; bool_y_stride = False
  if ((glb_pic_size[0] - localPicSize[0])%stride >= stride/2):
    nbr_of_elements_x += 1
    x_stride = (glb_pic_size[0] - localPicSize[0])%stride
    bool_x_stride = True
  if ((glb_pic_size[1] - localPicSize[1])%stride >= stride/2):
    nbr_of_elements_y += 1
    y_stride = (glb_pic_size[1] - localPicSize[1])%stride
    bool_y_stride = True

  total_nbr_elem = nbr_of_elements_x * nbr_of_elements_y

  ## adjust labels tabel
  # change dimension: e.g. if ymin = 1545 -> min_pos_y = 10 (which corresponds to the 11th element which not exist)
  # ONLY IF bool_y_stride = false or bool_x_stride = false respectively
  # -> if ymin > (nbr_of_elements_y - 1) * stride + localPicSize[1] (900+640 = 1540) then remove row
  # -> Drop row 

  # remove row where border of label is to close to the edge if stride didn't change for the last picture
  if (not bool_x_stride):
    labels.drop(labels.loc[labels['xmin'] >= (nbr_of_elements_x - 1) * stride + localPicSize[0]].index, inplace=True)
  if (not bool_y_stride):
    labels.drop(labels.loc[labels['ymin'] >= (nbr_of_elements_y - 1) * stride + localPicSize[1]].index, inplace=True)

  ## calculate grid position of range of label
  # x-positions (in grid starting by [0,0])
  labels['min_pos_x'] = np.fmax([0],np.ceil((labels['xmin'] - localPicSize[0])/stride)).astype(int)
  labels['max_pos_x'] = np.fmin([nbr_of_elements_x -1],np.floor(labels['xmax']/stride)).astype(int)
  # check for last Element with different stride if it is in range of label-borders
  if (bool_x_stride):
    mask = (labels['xmax'] >= (nbr_of_elements_x-2)*stride + x_stride) & (labels['xmax'] < (nbr_of_elements_x-1)*stride)
    labels.loc[mask, 'xmax'] = labels.loc[mask, 'xmax'] + 1

  # y-positions
  labels['min_pos_y'] = np.fmax([0],np.ceil((labels['ymin'] - localPicSize[1])/stride)).astype(int)
  labels['max_pos_y'] = np.fmin([nbr_of_elements_y-1], np.floor(labels['ymax']/stride)).astype(int)
  if (bool_y_stride):
    mask = (labels['ymax'] >= (nbr_of_elements_y-2)*stride + y_stride) & (labels['ymax'] < (nbr_of_elements_y-1)*stride)
    labels.loc[mask, 'ymax'] = labels.loc[mask, 'ymax'] + 1

  ## Iterate ofer all pictures to get csv file with there label
  # -> make df for each picture -> iterate over all pictures
  nbr_of_df = 0;
  for i in range (1,total_nbr_elem + 1):

    ## Coordinates and dimensions 
    # get grid coordinates starting by [0,0]
    grid_coord = [(np.floor((i-1)/nbr_of_elements_y)).astype(int), (i-1) % nbr_of_elements_y]

    # get position of recent picture
    # -> check for changed stride 
    if(bool_x_stride & (grid_coord[0] == nbr_of_elements_x - 1)):
      x_min = stride*(grid_coord[0]-1) + x_stride
    else:
      x_min = stride*grid_coord[0]
    
    x_max = x_min + localPicSize[0]

    if(bool_y_stride & (grid_coord[1] == nbr_of_elements_y - 1)):
      y_min = stride*(grid_coord[1]-1) + y_stride
    else:
      y_min = stride*grid_coord[1]

    y_max = y_min + localPicSize[0]

    #----------------------------------

    # check if its in range of local
    in_x_range = (labels['max_pos_x'] >= grid_coord[0]) & (labels['min_pos_x'] <= grid_coord[0])
    in_y_range = (labels['max_pos_y'] >= grid_coord[1]) & (labels['min_pos_y'] <= grid_coord[1])

    # file path for csv file 
    imageName = os.path.split(sourceImage)[1].split(".")[0];
    imageName += ("_" + str(grid_coord[0]) + "-" + str(grid_coord[1]))

    # get Data Frame with labels which match with coordinates 
    # check for a hit
    if ((in_x_range & in_y_range).any()):
      nbr_of_df +=1
      df = labels.loc[in_x_range & in_y_range]
      dim_y_df = df.shape[0]
      
      # only for checking (debugging)
      #df_old = df.copy()
      #-------------------
    
      # create new Data Frame for output
      df_out = pd.DataFrame(index=range(dim_y_df), columns = df.columns[:8])

      # add fixed values to df
      df_out[df.columns[0]] = imageName + '_' + str(i) # needs to fit with the actual name
      df_out[df.columns[1]] = localPicSize[0]
      df_out[df.columns[2]] = localPicSize[1]
      df_out[df.columns[3]] = label

      # get values from Data Frame df 
      x_min_df = df['xmin'].to_numpy()
      x_max_df = df['xmax'].to_numpy()
      y_min_df = df['ymin'].to_numpy()
      y_max_df = df['ymax'].to_numpy()

      # iterate over arrays (same size) to update borders of labels
      # xmax if x_max > xmax else x_max etc.
      for j in range(x_min_df.size):
        # set xmax
        if(x_max_df[j] >= x_max):
          x_max_df[j] = localPicSize[0]
        else:
          x_max_df[j] = x_max_df[j] - x_min
        # set xmin
        if(x_min > x_min_df[j]):
          x_min_df[j] = 0
        else:
          x_min_df[j] = x_min_df[j] - x_min
        # set ymax
        if(y_max_df[j] > y_max):
          y_max_df[j] = localPicSize[1]
        else:
          y_max_df[j] = y_max_df[j] - y_min
        # set ymin
        if(y_min > y_min_df[j]):
          y_min_df[j] = 0
        else:
          y_min_df[j] = y_min_df[j]  - y_min

      # update output Data Frame
      df_out['xmin'] = x_min_df
      df_out['xmax'] = x_max_df
      df_out['ymin'] = y_min_df
      df_out['ymax'] = y_max_df

      # optional: if distance between xmax and xmin to small -> drop column
      mask = ((df_out['xmax']-df_out['xmin']) < minLblOverlap) | ((df_out['ymax']-df_out['ymin']) < minLblOverlap)
      df_out.drop(df_out.loc[mask].index, inplace=True)

      # exporting csv file 
      csvFilepath = os.path.join(targetDir,(imageName + ".csv"))
      df_out.to_csv(csvFilepath, index=False, sep=';') 

    # If no labels match the image, create empty .csv and save it separately
    else:
      df = labels.loc[in_x_range & in_y_range]
      dim_y_df = df.shape[0]
      df_out = pd.DataFrame(index=range(dim_y_df), columns = df.columns[:8])

      csvFilepath = os.path.join(emptyDir,(imageName + ".csv"))
      df_out.to_csv(csvFilepath, index=False, sep=';')
    

sourceImage = r"ImagesRaw\Sejong_2013_1.png";
sourceFile = r"LabelsRaw\labels_UL.csv";
targetDir = r"LabelsCropped\LabelsTarget";
emptyDir = r"LabelsCropped\LabelsEmpty";

createLabelCSVForCroppedImage(sourceFile,sourceImage,targetDir,emptyDir,[640,640],100,10,"HR_building")
