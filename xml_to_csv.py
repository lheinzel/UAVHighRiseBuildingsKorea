import os
import glob
import pandas as pd
import xml.etree.ElementTree as ET

def xml_to_csv(xmlFilePath):
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
    return xml_df


def main():
    image_path = "LabelsRaw/Sejong_2013_1_UL.xml";
    targetFile = "LabelsRaw/labels_UL.csv";
    xml_df = xml_to_csv(image_path)
    xml_df.to_csv(targetFile, index=None, sep= ';')
    print('Successfully converted xml to csv.')

if __name__=="__main__":
    main();
