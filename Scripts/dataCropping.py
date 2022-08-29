from cgitb import small
from PIL import Image as Img
import os
import math
import pandas as pd
import xml.etree.ElementTree as ET


class UniformGridSlices:
    def __init__(self, fullRange, baseDims):
        self.fullRange = fullRange
        self.baseDims = baseDims
        self.gridDims = [0,0]
        self.border = [0,0]
        self.fillIn = [0,0]

        self.calculateGridDims();

    def calculateGridDims(self):
        self.gridDims[0] = math.floor(self.fullRange[0]/self.baseDims[0])
        self.border[0] = self.fullRange[0]%self.baseDims[0]%self.gridDims[0]
        self.fillIn[0] = math.floor(self.fullRange[0]%self.baseDims[0]/self.gridDims[0])

        self.gridDims[1] = math.floor(self.fullRange[1]/self.baseDims[1])
        self.border[1] = self.fullRange[1]%self.baseDims[1]%self.gridDims[1]
        self.fillIn[1] = math.floor(self.fullRange[1]%self.baseDims[1]/self.gridDims[1])

    def getOffset(self, indX, indY):
        offset = [0,0]

        if indX > 0:
            offset[0] = indX*self.baseDims[0]+indX*self.fillIn[0]

        if indY > 0:
            offset[1] = indY*self.baseDims[1]+indY*self.fillIn[1]

        return offset

    def getSize(self, indX, indY):
        size = self.baseDims[:]
        size[0] += self.fillIn[0] if indX < self.gridDims[0]-1 or self.border[0] == 0 else self.fillIn[0] + self.border[0]
        size[1] += self.fillIn[1] if indY < self.gridDims[1]-1 or self.border[1] == 0 else self.border[1] + self.fillIn[1]

        return size




def generateCroppedImages(sourcePath, targetPath, imgDims, imgFileExt):
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
            os.makedirs(targetPathCurrent);

        # Create UniformGridSlices Object for the cropping of the image
        imgSlicesCurrent = UniformGridSlices([imageCurrent.width, imageCurrent.height], imgDims)

        print("Cropping file: " + pictureFile  + "(w,h)=(" + str(imageCurrent.width) + "," + str(imageCurrent.height) + ") to " + str(imgSlicesCurrent.gridDims[0])\
              + "x" + str(imgSlicesCurrent.gridDims[1]) + " slices. Oversize: " + str(imgSlicesCurrent.fillIn))

        
        # Iterate over the two dimensions of the image and create the cropped parts. Save them to directories with
        # the same name as the source
        for indX in range(imgSlicesCurrent.gridDims[0]):

            for indY in range(imgSlicesCurrent.gridDims[1]):
                fNameImgCropped = pictureFile.split(".")[0] + "_" + str(indX) + "-" + str(indY) + "." + imgFileExt;
                fPathImgCropped = os.path.join(targetPathCurrent,fNameImgCropped);
                # Get the offset of the current cropped image w.r.t zero
                imgOffset = imgSlicesCurrent.getOffset(indX, indY)
                imgSize = imgSlicesCurrent.getSize(indX, indY)

                imgCropped = imageCurrent.crop((imgOffset[0],imgOffset[1],imgOffset[0]+imgSize[0],imgOffset[1]+imgSize[1]));
                imgCropped.save(fPathImgCropped);

    return;


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
    return xml_df

def createAnnotationForCroppedImage(lblSrcDf, imgSrcSlices, minOverlap, indX, indY, imgCrpFileName, imgFileExt):
    # get all all labels, that are in the range of the current cropped image
    imgOffset = imgSrcSlices.getOffset(indX, indY)
    imgSize = imgSrcSlices.getSize(indX, indY)

    # Get matching labels
    bLblInXRange = (lblSrcDf["xmax"] >= imgOffset[0]) & (lblSrcDf["xmin"] < (imgOffset[0] + imgSize[0]))
    bLblInYRange = (lblSrcDf["ymax"] >= imgOffset[1]) & (lblSrcDf["ymin"] < (imgOffset[1] + imgSize[1]))

    if (bLblInXRange & bLblInYRange).any():
        dfLblMatching = lblSrcDf.loc[bLblInXRange & bLblInYRange]
    else:
        dfLblMatching = pd.DataFrame(columns = lblSrcDf.columns)

    dfLblCrp = pd.DataFrame(index = range(dfLblMatching.shape[0]), columns = dfLblMatching.columns)

    # Set the metadata
    dfLblCrp["filename"] = imgCrpFileName
    dfLblCrp["width"] = imgSize[0]
    dfLblCrp["height"] = imgSize[1]
    dfLblCrp["class"] = dfLblMatching["class"].values

    # Set min and max values for each box
    xMinBox = dfLblMatching["xmin"].to_numpy();
    xMaxBox = dfLblMatching["xmax"].to_numpy();
    yMinBox = dfLblMatching["ymin"].to_numpy();
    yMaxBox = dfLblMatching["ymax"].to_numpy();

    # Calculate location and dimensions of bounding boxes
    for i in range(dfLblCrp.shape[0]):
        xMinBox[i] = (xMinBox[i] - imgOffset[0]) if xMinBox[i] >= imgOffset[0] else 0
        xMaxBox[i] = (xMaxBox[i] - imgOffset[0]) if xMaxBox[i] < (imgOffset[0] + imgSize[0]) else imgSize[0] - 1
        yMinBox[i] = (yMinBox[i] - imgOffset[1]) if yMinBox[i] >= imgOffset[1] else 0
        yMaxBox[i] = (yMaxBox[i] - imgOffset[1]) if yMaxBox[i] < (imgOffset[1] + imgSize[1]) else imgSize[1] - 1

    # Save the bounding boxes
    dfLblCrp["xmin"] = xMinBox
    dfLblCrp["xmax"] = xMaxBox
    dfLblCrp["ymin"] = yMinBox
    dfLblCrp["ymax"] = yMaxBox

    if (indX == 1 and indY==2):
        print(dfLblCrp)

    # Delete labels with too small overlap
    dfLblCrp.drop(dfLblCrp[(dfLblCrp["xmax"] - dfLblCrp["xmin"]) < minOverlap].index, inplace=True)
    dfLblCrp.drop(dfLblCrp[(dfLblCrp["ymax"] - dfLblCrp["ymin"]) < minOverlap].index, inplace=True)

    if (indX == 1 and indY==2):
        print(dfLblCrp)
    
    return dfLblCrp

def distributeLabels(lblSrcDir, lblCrpDir, fldNameEmpty, fldNameNonEmpty, imgSrcDir, imgCrpDims, imgFileExt, minOverlap = 10):
   
    for el in os.scandir(lblSrcDir):
        if el.is_file() and el.name.split(".")[1] == "xml":
            # Get Source Annotation as dataframe
            lblSrcDf = xml_to_csv(el.path, os.path.join(lblSrcDir, el.name.split(".")[0] + ".csv"))

            # Open matching source image and create object for partitioning
            imgSrcPath = os.path.join(imgSrcDir, el.name.split(".")[0] + "." + imgFileExt)
            imgSrc = Img.open(imgSrcPath)
            imgSrcSlices = UniformGridSlices([imgSrc.width, imgSrc.height], imgCrpDims)

            # Create directories for labels
            imgFileName = el.name.split(".")[0]
            lblCrpEmptyDir = os.path.join(lblCrpDir,fldNameEmpty, imgFileName)
            lblCrpNonEmptyDir = os.path.join(lblCrpDir, fldNameNonEmpty, imgFileName)

            if not os.path.exists(lblCrpEmptyDir):
                os.makedirs(lblCrpEmptyDir)
            if not os.path.exists(lblCrpNonEmptyDir):
                os.makedirs(lblCrpNonEmptyDir)

            print("Distributing Labels and boxes for file " + imgFileName + "...")

            for indX in range(imgSrcSlices.gridDims[0]):
                for indY in range(imgSrcSlices.gridDims[1]):
                    lblCrpFileName = imgFileName + "_" + str(indX) + "-" + str(indY)
                    # create dataframe for current cropped image
                    dfLblCrp = createAnnotationForCroppedImage(lblSrcDf, imgSrcSlices, minOverlap, indX, indY, lblCrpFileName + "." + imgFileExt, imgFileExt)

                    if dfLblCrp.empty:
                        dfLblCrp.to_csv(os.path.join(lblCrpEmptyDir, lblCrpFileName + ".csv"), index=False, sep=';')
                    else:
                        dfLblCrp.to_csv(os.path.join(lblCrpNonEmptyDir, lblCrpFileName + ".csv"), index=False, sep=';')

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


def verifyCroppedFiles(lblTargetDir, imgTargetDir, fldNameEmpty, fldNameNonEmpty, imgFileExt):
    print("Verifying Cropped files...")
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



if __name__ == "__main__":
    imgSourcePath = r"DataRaw/Images"
    lblSourcePath = r"DataRaw/Labels"
    imgTargetPath = r"DataCropped_320x320/Images"
    lblTargetpath = r"DataCropped_320x320/Labels"
    imgDims = [320,320]
    imgFileExt = "png"

    generateCroppedImages(imgSourcePath, imgTargetPath, imgDims, imgFileExt)

    distributeLabels(lblSourcePath, lblTargetpath, "Empty", "Detection", imgSourcePath, [320,320], "png")

    separateCroppedImagaes(lblTargetpath, imgTargetPath, "Empty", "Detection")

    verifyCroppedFiles(lblTargetpath, imgTargetPath, "Empty", "Detection", "png")