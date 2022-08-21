from asyncio import gather
from multiprocessing.sharedctypes import Value
from turtle import end_fill
from xml.dom import HierarchyRequestErr
from PIL import Image as Img
import os
import math
import numpy as np
import pandas as pd
import glob
import xml.etree.ElementTree as ET

def initDirectories(listDirs):
    for dir in listDirs:
        
        if not os.path.exists(dir):
            os.mkdir(listDirs);
        


def generateCroppedImages(sourcePath, targetPath, dimX, dimY, strideX, strideY, imgFileExt):
    # Get files in directory
    sourceNames = [elem for elem in os.listdir(sourcePath) if elem.split(".")[1] == imgFileExt];

    # raise error if no .png files found
    if not sourceNames:
        raise ValueError("No appropriate .png files in directory: " + sourcePath);

    # crop all picture files
    for pictureFile in sourceNames:

        # open current file as image
        fileCurrent = os.path.join(sourcePath,pictureFile);
        imageCurrent = Img.open(fileCurrent);

        # create target directory if not present
        targetPathCurrent = os.path.join(targetPath,pictureFile.split(".")[0]);
        if not os.path.exists(targetPathCurrent):
            os.mkdir(targetPathCurrent);

        # calculate number of slices in width and heigth direction
        nSlicesX = math.ceil((imageCurrent.width - dimX)/strideX)+1;
        nSlicesY = math.ceil((imageCurrent.height - dimY)/strideY)+1;

        # Smaller stride on the borders to utilize the whole image
        stdRX = (imageCurrent.width - dimX)%strideX;
        stdRY = (imageCurrent.height - dimY)%strideY;

        # If the stride on the border images (difference to the previous image regarding translation) is too small,
        # do not utilize the border regions
        if stdRX < strideX/2:
          stdRX = 0;
          nSlicesX -= 1;

        if stdRY < strideY/2:
            stdRY = 0;
            nSlicesY -= 1;


        print("Cropping file: " + pictureFile  + "(w,h)=(" + str(imageCurrent.width) + "," + str(imageCurrent.height) + ") to " + str(nSlicesX) + "x" + str(nSlicesY) + " slices. Border strides: stdrRX=" + str(stdRX) + " stdrRY=" + str(stdRY)  );

        xStart = 0;
        yStart = 0;
        # Iterate over the two dimensions of the image and create the cropped parts. Save them to directories with
        # the same name as the source
        for indX in range(nSlicesX):
            strdXCurrent = strideX if (indX < nSlicesX-2 or stdRX == 0) else stdRX;

            for indY in range(nSlicesY):
                strdYCurrent = strideY if (indY < nSlicesY-2 or stdRY == 0) else stdRY;
                fNameImgCropped = pictureFile.split(".")[0] + "_" + str(indX) + "-" + str(indY) + "." + imgFileExt;
                fPathImgCropped = os.path.join(targetPathCurrent,fNameImgCropped);
                imgCropped = imageCurrent.crop((xStart,yStart,xStart+dimX,yStart+dimY));
                imgCropped.save(fPathImgCropped);

                yStart += strdYCurrent;

            xStart += strdXCurrent;
            yStart = 0;

  
    return;


def initDirectories(listDirs):
    for dir in listDirs:
        if not os.path.exists(dir):
            os.makedirs(dir,exist_ok=True);


def xml_to_csv(xmlFilePath, targetFilePath):
    dataList = [];
    tree = ET.parse(xmlFilePath)
    root = tree.getroot()
    for member in root.findall('object'):
        value = (root.find('filename').text,
                    int(root.find('size')[0].text),
                    int(root.find('size')[1].text),
                    member[0].text,
                    int(member[4][0].text),
                    int(member[4][1].text),
                    int(member[4][2].text),
                    int(member[4][3].text)
                    )
        dataList.append(value);
        
    column_name = ['filename', 'width', 'height', 'class', 'xmin', 'ymin', 'xmax', 'ymax']
    xml_df = pd.DataFrame(dataList,columns=column_name)
    xml_df.to_csv(targetFilePath, index=None, sep= ';')


def createLabelCSVForCroppedImages(sourceFile, sourceImage, targetDir, emptyDir, localPicSize, stride, label):
  #read-in csv-file with labels from original picture
  labels = pd.read_csv(sourceFile, delimiter = ';')

  #read-in original image 
  im_png = Img.open(sourceImage)
  im_as_array = np.array(im_png)

  #---------------------------------------------------
  ## calculate shapes

  #get x and y dimension of image: [x,y]
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

    # name of the image 
    imageName = os.path.split(sourceImage)[1].split(".")[0];
    imageName += ("_" + str(grid_coord[0]) + "-" + str(grid_coord[1]))

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

    # get Data Frame with labels which match with coordinates 
    # check for a hit
    nbr_of_df +=1

    if ((in_x_range & in_y_range).any()):
      df = labels.loc[in_x_range & in_y_range]
    else:
      df = pd.DataFrame(columns=labels.columns)

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

    # exporting csv file 
    if df_out.empty:
      csvFilepath = os.path.join(emptyDir,(imageName + ".csv"))
      df_out.to_csv(csvFilepath, index=False, sep=';') 
    else:
      csvFilepath = os.path.join(targetDir,(imageName + ".csv"))
      df_out.to_csv(csvFilepath, index=False, sep=';') 
 


def distributeLabels(lblSourceDir, imgSourceDir, lblDir, fldNameEmpty, fldNameNonempty ,localPicSize, stride, label, imgFileExt): 
  
  # iterate over all label xmls
  lblFileList = os.listdir(lblSourceDir);
  for fname in lblFileList:

    if fname.split(".")[1] == "xml":
        # directories for the label .csv files
        imageName = os.path.split(fname)[1].split(".")[0]
        targetDir = os.path.join(lblDir,fldNameNonempty,imageName)
        emptyDir = os.path.join(lblDir, fldNameEmpty ,imageName)
        lblSourceFile = os.path.join(lblSourceDir,fname);
        imgSourceFile = os.path.join(imgSourceDir,imageName) + "." + imgFileExt;

        # Convert the xml to a csv file
        pathCSVFull = os.path.join(os.path.split(lblSourceFile)[0],(imageName + "_lbl.csv"))
        xml_to_csv(lblSourceFile, pathCSVFull)

        # Create directories if not exist
        initDirectories([targetDir,emptyDir])

        # Create the .csv files of the labels for the cropped images
        createLabelCSVForCroppedImages(pathCSVFull,imgSourceFile,targetDir,emptyDir,localPicSize,stride,label)



def separateCroppedImagaes(lblTargetDir, imgTargetDir, fldNameEmpty, fldNameNonEmpty):
  imgEmptyDir = os.path.join(imgTargetDir, fldNameEmpty)
  lblEmptyDir = os.path.join(lblTargetDir, fldNameEmpty)
  imgDetectDir = os.path.join(imgTargetDir, fldNameNonEmpty)
  lblDetectDir = os.path.join(lblTargetDir, fldNameNonEmpty);

  if not os.path.exists(imgEmptyDir):
    os.makedirs(imgEmptyDir)

  # Iterate over the folders containing the empty cropped images of each raw image
  for el in os.listdir(lblEmptyDir):
    if os.path.isdir(os.path.join(lblEmptyDir,el)):
        picDirTarget = os.path.join(imgEmptyDir, el)
        picDirSource = os.path.join(imgTargetDir, el)

        # create folder for empty cropped images
        if not os.path.exists(picDirTarget):
          os.makedirs(picDirTarget)

        # extract cropped images
        for lbl in os.listdir(os.path.join(lblEmptyDir, el)):
          sourcePicPath = os.path.join(picDirSource, lbl.split(".")[0]+".png")
          targetPicPath = os.path.join(picDirTarget, lbl.split(".")[0]+".png")

          if os.path.exists(sourcePicPath):
            os.rename(sourcePicPath, targetPicPath)

  # copy the folders containing the nonempty cropped images in a separate directory
  if not os.path.exists(imgDetectDir):
    os.makedirs(imgDetectDir)

  for el in os.listdir(imgTargetDir):
    if os.path.isdir(os.path.join(imgTargetDir, el)) and not el == fldNameEmpty and not el == fldNameNonEmpty:
      os.rename(os.path.join(imgTargetDir, el), os.path.join(imgTargetDir, fldNameNonEmpty, el))


def gatherDirContents(targetDir, fileExt):
  fileList = []; 

  for el in os.listdir(targetDir):
    subdirCurrent = os.path.join(targetDir, el)

    if os.path.isdir(subdirCurrent):

      for f in os.listdir(subdirCurrent):
        if f.split(".")[1] == fileExt:
          fileList.append(os.path.join(el, f))

  return fileList;


def verifyAugmentedFiles(lblTargetDir, imgTargetDir, fldNameEmpty, fldNameNonEmpty, imgFileExt):
  lblEmptyDir = os.path.join(lblTargetDir, fldNameEmpty)
  imgEmptyDir = os.path.join(imgTargetDir, fldNameEmpty)
  lblNonEmptyDir = os.path.join(lblTargetDir, fldNameNonEmpty)
  imgNonEmptyDir = os.path.join(imgTargetDir, fldNameNonEmpty)

  # Check if nonempty image and label files match
  lblNonEmpty = gatherDirContents(lblNonEmptyDir, "csv")
  imgNonEmpty = gatherDirContents(imgNonEmptyDir, imgFileExt)

  if len(lblNonEmpty) != len(imgNonEmpty):
    raise ValueError("Numer of files in " + lblNonEmptyDir + " noes not match " + imgNonEmptyDir + "!")
  else:
    for pic in imgNonEmpty:
      lblCurrent = pic.split(".")[0] + ".csv"

      if not lblCurrent in lblNonEmpty:
        raise ValueError("No matching Label file found for " + pic + "!")

  # Check if empty image and label files match
  lblEmpty = gatherDirContents(lblEmptyDir, "csv")
  imgEmpty = gatherDirContents(imgEmptyDir, imgFileExt)

  if len(lblEmpty) != len(imgEmpty):
    raise ValueError("Numer of files in " + lblEmptyDir + " noes not match " + imgEmptyDir + "!")
  else:
    for pic in imgEmpty:
      lblCurrent = pic.split(".")[0] + ".csv"

      if not lblCurrent in lblEmpty:
        raise ValueError("No matchin Label file found for " + pic +"!")





if __name__ == "__main__" :
    pathPictureSource = r"DataRaw/Images";
    pathPictureTarget = r"DataAugmented/Images";
    pathLabelSource = r"DataRaw/Labels";
    pathLabelTarget = r"DataAugmented/Labels";
    fldNameEmpty = "Empty";
    fldNameNonEmpty = "Detection"

    generateCroppedImages(pathPictureSource, pathPictureTarget, 640, 640, 100, 100, "png")

    distributeLabels(pathLabelSource, pathPictureSource, pathLabelTarget, "Empty", "Detection", [640,640], 100, "HR_building", "png")

    separateCroppedImagaes(pathLabelTarget, pathPictureTarget, fldNameEmpty, fldNameNonEmpty);

    verifyAugmentedFiles(pathLabelTarget, pathPictureTarget, fldNameEmpty, fldNameNonEmpty, "png")

    




    
    
    








