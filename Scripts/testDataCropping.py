from genericpath import isfile
from tkinter import Image
from PIL import Image as Img
from PIL import ImageDraw as ImageDraw
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import xml.etree.ElementTree as ET
from dataCropping import generateCroppedImages
from dataCropping import UniformGridSlices
from dataCropping import distributeLabels
import shutil as sh

def combineCroppedImages(imgCroppedDir, refDim, crpDim, imgFileExt):
    imgComb = Img.new('RGB',(refDim[0],refDim[1]))

    imgSlices = UniformGridSlices(refDim, crpDim)

    for el in os.scandir(imgCroppedDir):
        if el.is_file() and el.name.split(".")[1] == imgFileExt:
            strGridDims = el.name.split(".")[0].split("_")[-1]
            gridDimsCur = [int(strGridDims.split("-")[0]), int(strGridDims.split("-")[1])]
            imgCur = Img.open(el.path)

            offset = imgSlices.getOffset(gridDimsCur[0],gridDimsCur[1])
            imgComb.paste(imgCur, (offset[0],offset[1]))

    return imgComb




def checkMatchForCroppedImages(imgSourcePath, targetDir, crpDim, imgFileExt):
    refImage = Img.open(imgSourcePath)
    tstImage = combineCroppedImages(targetDir, [refImage.width, refImage.height], crpDim, imgFileExt)

    f, axarr = plt.subplots(1,2)
    axarr[0].imshow(tstImage)
    axarr[1].imshow(refImage)
    plt.show()

    return list(refImage.getdata()) == list(tstImage.getdata())

def testImageCropping(imgSourceDir, imgCroppedDir, crpDim, imgFileExt):
    print("--- Start testImageCropping ---")
    
    if os.path.exists(imgCroppedDir):
        sh.rmtree(imgCroppedDir)

    generateCroppedImages(imgSourceDir, imgCroppedDir, [320, 320], imgFileExt)

    for el in os.scandir(imgSourceDir):
        
        if el.is_file() and el.name.split(".")[1] == imgFileExt:
            print("Testing file " + el.name + "...")
            targetPath = os.path.join(imgCroppedDir, el.name.split(".")[0])

            if not os.path.exists(targetPath):
                raise ValueError("Cropped file directory " + targetPath + " does not exist!")

            else:
                bMatch = checkMatchForCroppedImages(el.path, targetPath, crpDim, imgFileExt)
                if not bMatch:
                    raise ValueError("Cropped images do not match " + el.name)


def visualizeImagAnnotation(imagePath, labelPath, resImagePath):
    if not os.path.exists(os.path.dirname(resImagePath)):
        os.makedirs(os.path.dirname(resImagePath))

    labels = pd.read_csv(labelPath, delimiter=";")
    imgCurrent = Img.open(imagePath)
    imgDrawCurr = ImageDraw.Draw(imgCurrent)

    for index, row in labels.iterrows():
        width = row['xmax'] - row['xmin']
        height = row['ymax'] - row['ymin']
        box = [(row["xmin"],row["ymin"]), (row["xmax"],row["ymax"])]
        imgDrawCurr.rectangle(box, outline="red")
        
    imgCurrent.save(resImagePath)
  
     
    
def visualizeAnnotationFullImages(imgSrcDir, lblSrcDir, imgFullDir, imgFileExt):
    for el in os.scandir(imgSrcDir):
        if el.is_file() and el.name.split(".")[1] == imgFileExt:
            lblPath = os.path.join(lblSrcDir, el.name.split(".")[0] + ".csv")
            resPath = os.path.join(imgFullDir, el.name)
            
            visualizeImagAnnotation(el.path, lblPath, resPath)

def visualizeAnnotationCroppedImages(imgCrpDir, lblCrpDir, imgFileExt):
    for el in os.scandir(imgCrpDir):
        if el.is_dir():
            
            for f in os.scandir(el.path):
                if f.is_file() and f.name.split(".")[1] == imgFileExt:
                    lblPath = os.path.join(lblCrpDir, el.name, f.name.split(".")[0] + ".csv")
                    if os.path.exists(lblPath):
                        visualizeImagAnnotation(f.path, lblPath, f.path)
                    


def testLabelDistribution(imgSrcDir, imgCrpDir, imgFullDir, lblSrcDir, lblCrpDir, imgCrpDims, imgFileExt):
    print("-- Start testLabelDistribution --")

    # Crop the data
    if os.path.exists(imgCrpDir):
        sh.rmtree(imgCrpDir)

    generateCroppedImages(imgSrcDir, imgCrpDir,imgCrpDims, imgFileExt)

    if os.path.exists(lblCrpDir):
        sh.rmtree(lblCrpDir)

    distributeLabels(lblSrcDir, lblCrpDir, "Empty", "Detection", imgSrcDir, imgCrpDims, imgFileExt, 0)

    if os.path.exists(imgFullDir):
        sh.rmtree(imgFullDir)

    # Create Full Images with visualization of annotations
    visualizeAnnotationFullImages(imgSrcDir, lblSrcDir,  imgFullDir, imgFileExt)
    
    # Create Cropped images with visualization of annotations (overwrite blank cropped images)
    visualizeAnnotationCroppedImages(imgCrpDir, os.path.join(lblCrpDir, "Detection"), imgFileExt)

    # Test match 
    for el in os.scandir(imgFullDir):
        
        if el.is_file() and el.name.split(".")[1] == imgFileExt:
            print("Testing file " + el.name + "...")
            targetPath = os.path.join(imgCrpDir, el.name.split(".")[0])

            if not os.path.exists(targetPath):
                raise ValueError("Cropped file directory " + targetPath + " does not exist!")

            else:
                bMatch = checkMatchForCroppedImages(el.path, targetPath, imgCrpDims, imgFileExt)
                pass


if __name__ == "__main__":
    imgCroppedDir = r"DataCroppedTest/ImageCropping"
    imgSourceDir = r"DataRaw/Images"
    lblSourceDir = r"DataRaw/Labels"
    imgFileExt = "png"

    imgFullDir = r"DataCroppedTest/LabelDistribution/ImagesFull"
    imgCroppedDirDistr = r"DataCroppedTest/LabelDistribution/ImagesCropped"
    lblCroppedDir = r"DataCroppedTest/LabelDistribution/Labels"

    #testImageCropping(imgSourceDir, imgCroppedDir, [320,320], imgFileExt)

    testLabelDistribution(imgSourceDir, imgCroppedDirDistr, imgFullDir, lblSourceDir, lblCroppedDir, [320, 320], "png")


