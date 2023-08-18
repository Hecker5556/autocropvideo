import cv2
import numpy as np
from random import randint
from PIL import Image
import subprocess
import argparse
class autocrop:
    def __init__(self, filename: str, threshold: int = None, framestoanalyze: int = None, deletetemp: bool = True) -> None:
        self.threshold = threshold if threshold else 10
        self.framestoanalyze = framestoanalyze if framestoanalyze else 5
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
                actualwidth = np.mean(widths)
                actualheight = np.mean(heights)
        if not actualwidth:
            actualwidth = widths[0]
            actualheight = heights[0]
        output = self.cropvideo(width=actualwidth, height=actualheight)
        if deletetemp:
            import os
            for i in os.listdir():
                if i.startswith('cropped') or i.startswith('thing'):
                    os.remove(i)
        return output

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
        _,thresh = cv2.threshold(gray,self.threshold,255,cv2.THRESH_BINARY)
        contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cnt = contours[0]
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
        subprocess.run(f'ffmpeg -i {self.videofilename} -vf crop={width}:{height} -y output.mp4'.split())
        return 'output.mp4'
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='autocrop a video with changeable threshold and amount of frames to analyze')
    parser.add_argument('-file', '-i', help='filepath to video')
    parser.add_argument('-threshold', '-t', type=int, help='threshold, between 1-20 is recommended, default 10')
    parser.add_argument('-amountframes', '-f', type=int, help='amount frames to analyze (picked at random, default 5)')
    parser.add_argument('-deletetemp', '-d', action='store_true', help='whether to delete temporary files used')
    args = parser.parse_args()
    autocrop(filename=args.file, threshold=args.threshold, framestoanalyze=args.amountframes, deletetemp=args.deletetemp)