import cv2, os
import numpy as np
from random import randint
from PIL import Image
import subprocess
import argparse
from typing import Literal
import requests
class autocrop:
    def __init__(self, filename: str, threshold: int = None, color_to_crop: Literal['black', 'white'] = None,
                 framestoanalyze: int = None, deletetemp: bool = True,
                 handlecrop: bool = False) -> None:
        if threshold:
            if color_to_crop and color_to_crop == "white":
                self.threshold = 255 - threshold
            else:
                self.threshold = threshold
        else:
            if color_to_crop and color_to_crop == "white":
                self.threshold = 240
            else:
                self.threshold = 10
        if deletetemp == None:
            deletetemp = True
        self.color = color_to_crop if color_to_crop else 'black'
        self.framestoanalyze = framestoanalyze if framestoanalyze else 5
        if not os.path.exists(filename):
            if filename.startswith("https"):
                with open("tempfile", 'wb') as f1:
                    for data in requests.get(filename, stream=True).iter_content(1024):
                        f1.write(data)
                filename = "tempfile"
            else:
                raise FileNotFoundError(f"Couldnt find such a file")
        self.videofilename = filename
        self.frames = self.get_frame_count()
        filepaths = []
        for i in range(self.framestoanalyze):
            framenumber = randint(1, self.frames)
            self.save_frame(output_path=f'thing{i}.png', frame_num=framenumber)
            filepaths.append(f'thing{i}.png')
        results = []
        for i in filepaths:
            results.append(self.cropimage(filepath=i))
        widths = []
        heights = []
        for i in results:
            width, height = self.getimagesize(i)
            widths.append(width)
            heights.append(height)
            previouswidth = 'no'
            previousheight = 'no'
            actualwidth = None
        for index, (width, height) in enumerate(zip(widths, heights)):
            if width < 10 or height < 10:
                widths.pop(index)
                heights.pop(index)
                continue
            if previouswidth == 'no':
                previouswidth = width
                previousheight = height
            if width != previouswidth or height != previousheight:
                actualwidth = int(np.bincount(widths).argmax())
                actualheight = int(np.bincount(heights).argmax())
        if not actualwidth:
            actualwidth = widths[0]
            actualheight = heights[0]
        if not handlecrop:
            output = self.cropvideo(width=actualwidth, height=actualheight)
            self.outputfile = output

        self.width = actualwidth
        self.height = actualheight
        print(self.width, self.height)
        if deletetemp:
            for i in os.listdir():
                if i.startswith('cropped') or i.startswith('thing'):
                    os.remove(i)

        return None

    def get_frame_count(self):
        cap = cv2.VideoCapture(self.videofilename)
        if not cap.isOpened():
            raise ValueError("Unable to open video file")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        return frame_count

    def save_frame(self, output_path, frame_num):
        cap = cv2.VideoCapture(self.videofilename)
        
        if not cap.isOpened():
            print("Error opening video file.")
            return
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        
        ret, frame = cap.read()

        if not ret:
            print(f"Error reading frame {frame_num}.")
            return
        
        cv2.imwrite(output_path, frame)
        
        cap.release()


    def cropimage(self, filepath):
        img = cv2.imread(filepath)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        _,thresh = cv2.threshold(gray,self.threshold,255,cv2.THRESH_BINARY if self.color == "black" else cv2.THRESH_BINARY_INV)
        contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cnt = max(contours, key=cv2.contourArea)
        x,y,w,h = cv2.boundingRect(cnt)
        crop = img[y:y+h,x:x+w]
        cv2.imwrite(f'cropped{filepath}',crop)
        return f'cropped{filepath}'


    def getimagesize(self, croppedimagepath):
        image = Image.open(croppedimagepath)
        width, height = image.size
        return width, height

    def cropvideo(self, width, height):
        print(width, height)
        if width % 2 != 0:
            width = round(width/2)
        if height % 2 != 0:
            height = round(height/2)
        subprocess.run(f'ffmpeg -i {self.videofilename} -vf crop={width}:{height} -y output.mp4'.split())
        return 'output.mp4'
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='autocrop a video with changeable threshold and amount of frames to analyze')
    parser.add_argument('-file', '-i', help='filepath to video')
    parser.add_argument('-threshold', '-t', type=int, help='threshold, between 1-20 is recommended, default 10')
    parser.add_argument('-amountframes', '-f', type=int, help='amount frames to analyze (picked at random, default 5)')
    parser.add_argument('-deletetemp', '-d', action='store_true', help='whether to delete temporary files used')
    parser.add_argument('-handlecrop', '-hc', action="store_true", help='if you want to handle crop instead of using ffmpeg, use this, this will print out width and height')
    parser.add_argument('-color', '-c', type=str, help="color to crop, can only be white or black")
    args = parser.parse_args()
    if args.color:
        if args.color not in ["black", "white"]:
            raise ValueError("color needs to either be black or white")
    autocrop(filename=args.file, threshold=args.threshold, framestoanalyze=args.amountframes, deletetemp=args.deletetemp, color_to_crop=args.color)