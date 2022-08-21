import os
from tkinter import Grid
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from dataAugmentation import GridSlices


def visualizeLabeling(sourceImage, lblSource):
    fig = plt.figure();
    imgSource = Image.open(sourceImage)
    plt.imshow(imgSource)
    ax = plt.gca()

    labels = pd.read_csv(lblSource, delimiter=";")
    imgName = os.path.split(sourceImage)[1]
    labelDir = os.path.split(lblSource)[0]

    for index, row in labels.iterrows():
        width = row['xmax'] - row['xmin']
        height = row['ymax'] - row['ymin']
        box = patches.Rectangle((row["xmin"],row["ymin"]), width, height, linewidth=1, edgecolor='r', facecolor='none')

        ax.add_patch(box)

    plt.savefig(os.path.join(labelDir,imgName))
    plt.show()
 
    return


def visualizeLabeledCroppedImage(imagePath, labelPath, resultDir, sourceName):
    crpImagename = os.path.split(imagePath)[1]
    resImagePath = os.path.join(resultDir, sourceName, crpImagename)

    if not os.path.exists(os.path.dirname(resImagePath)):
        os.makedirs(os.path.dirname(resImagePath))

    labels = pd.read_csv(labelPath, delimiter=";")
    imgCurrent = Image.open(imagePath)
    plt.imshow(imgCurrent)
    ax = plt.gca()

    for index, row in labels.iterrows():
        width = row['xmax'] - row['xmin']
        height = row['ymax'] - row['ymin']
        box = patches.Rectangle((row["xmin"],row["ymin"]), width, height, linewidth=1, edgecolor='r', facecolor='none')
        ax.add_patch(box)
    
    plt.savefig(resImagePath)
    plt.cla()


def visualizeXBorderImages(indXMax, indYMax, imageDir, labelDir, resultDir, sourceName):
    for i in [0, indXMax]:
        for j in range(0, indYMax+1):
            imageName = sourceName + "_" + str(i) + "-" + str(j)

            imagePath = os.path.join(imageDir,(imageName + ".png"))
            labelPath = os.path.join(labelDir,(imageName + ".csv"))

            if os.path.exists(imagePath) and os.path.exists(labelPath):
                visualizeLabeledCroppedImage(imagePath, labelPath, resultDir, sourceName)


def visualizeYBorderImages(indXMax, indYMax, imageDir, labelDir, resultDir, sourceName):  
    for i in range(1, indXMax):
        for j in [0, indYMax]:
            imageName = sourceName + "_" + str(i) + "-" + str(j)

            imagePath = os.path.join(imageDir,(imageName + ".png"))
            labelPath = os.path.join(labelDir,sourceName,(imageName + ".csv"))

            if os.path.exists(imagePath) and os.path.exists(labelPath):
                visualizeLabeledCroppedImage(imagePath, labelPath, resultDir, sourceName)      

        
def visualizeDistributedLabeling(imageDir, labelDir, sourceDir, resultDir):
    for srcImage in os.listdir(sourceDir):
        if srcImage.split(".")[1] == "png":
            sourceName = srcImage.split(".")[0]
            imgDirCropped = os.path.join(imageDir, sourceName)
            lblDirCropped = os.path.join(labelDir, sourceName)
            lImagesCropped = os.listdir(imgDirCropped)

            lImageXCoords = []
            lImageYCoords = []

            for imgName in lImagesCropped:
                imgName = imgName.split(".")[0]
                imgCoords = imgName.split("_")[-1].split("-")
                lImageXCoords.append(int(imgCoords[0]))
                lImageYCoords.append(int(imgCoords[1]))
                
            indXMax = max(lImageXCoords)
            indYMax = max(lImageYCoords)

            visualizeXBorderImages(indXMax, indYMax, imgDirCropped, lblDirCropped, resultDir, sourceName)
            visualizeYBorderImages(indXMax, indYMax, imgDirCropped, lblDirCropped, resultDir, sourceName)


if __name__=="__main__":
    sourceImage = r"DataRaw\Images";
    imageDir = r"DataAugmented\Images\Detection";
    sourceFile = r"DataRaw\Labels\Seoul_2018_1.xml";
    labelDir = r"DataAugmented\Labels\Detection";
    testResDir = r"DataAugmented\Images\Test";

    visualizeDistributedLabeling(imageDir, labelDir, sourceImage, testResDir)