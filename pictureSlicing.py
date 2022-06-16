from xml.dom import HierarchyRequestErr
from PIL import Image as Img
import os
import math

def generateCroppedImages(sourcePath, targetPath, dimX, dimY, strideX, strideY):
    # Get files in directory
    sourceNames = [elem for elem in os.listdir(sourcePath) if elem.split(".")[1] == "png"];

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
        if stdRX < 50 or stdRY < 50:
            stdRX = 0;
            stdRY = 0;
            nSlicesX -= 1;
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
                fNameImgCropped = pictureFile.split(".")[0] + "_" + str(indX) + "-" + str(indY) + ".png";
                fPathImgCropped = os.path.join(targetPathCurrent,fNameImgCropped);
                imgCropped = imageCurrent.crop((xStart,yStart,xStart+dimX,yStart+dimY));
                #imgCropped.save(fPathImgCropped);

                yStart += strdYCurrent;

            xStart += strdXCurrent;
            yStart = 0;

  
    return;



if __name__ == "__main__" :
    pathSource = "ImagesRaw";
    pathTarget = "ImagesCropped";


    if not os.path.exists(pathTarget):
        os.mkdir(pathTarget);

    generateCroppedImages(pathSource, pathTarget, 640, 640, 100, 100);




    
    
    








