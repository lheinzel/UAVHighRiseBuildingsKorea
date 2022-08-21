import os
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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


def visualizeDistributedLabeling(imageDir, labelDir, sourceImage, imgRange, resultDir):
    sourceName = os.path.split(sourceImage)[1].split(".")[0]
    fig = plt.figure(2)
    # Iterate over the the grid in the specified range
    for indX in range(imgRange[0]):
        for indY in range(imgRange[1]):
            imageName = sourceName + "_" + str(indX) + "-" + str(indY)
            imagePath = os.path.join(imageDir,(imageName + ".png"))
            labelPath = os.path.join(labelDir,sourceName,(imageName + ".csv"))

            # display all labels if the label file exists
            if os.path.exists(labelPath):
                
                labels = pd.read_csv(labelPath, delimiter=";")
                imgCurrent = Image.open(imagePath)
                plt.imshow(imgCurrent)
                ax = plt.gca()

                for index, row in labels.iterrows():
                    width = row['xmax'] - row['xmin']
                    height = row['ymax'] - row['ymin']
                    box = patches.Rectangle((row["xmin"],row["ymin"]), width, height, linewidth=1, edgecolor='r', facecolor='none')
                    ax.add_patch(box)
                plt.show()
                plt.cla()
                
    return
        





if __name__=="__main__":
    sourceImage = r"DataRaw\Images\Sejong_2019_1";
    imageDir = r"DataAugmented\Images\Detection\Sejong_2019_1";
    sourceFile = r"DataRaw\Labels\Sejong_2019_1.xml";
    labelDir = r"DataAugmented\Labels\Detection";
    testResDir = r"LabelsCropped\LabelsTest";

    visualizeDistributedLabeling(imageDir, labelDir, sourceImage, [13,13], testResDir)