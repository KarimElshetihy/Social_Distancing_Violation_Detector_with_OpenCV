import social_distancing_config as config
from detection import detect_poeple
from scipy.spatial import distance as dist
import numpy as np 
import argparse
import cv2
import os


ap = argparse.ArgumentParser()

ap.add_argument('-i', '--input', type=str, default="Video/01.avi", help="path to input video file")
ap.add_argument('-o', '--output', type=str, default="Output/", help="path to output video file")
ap.add_argument('-d', '--display', type=int, default="1", help="Display Output Frame? (default=1)")

args = vars(ap.parse_args())

labelsPath = os.path.sep.join([config.MODEL_PATH, 'coco.names.txt'])
labels = open(labelsPath).read().strip().split(('\n'))

weightsPath = os.path.sep.join([config.MODEL_PATH, 'yolov3.weights'])
configPath = os.path.sep.join([config.MODEL_PATH, 'yolov3.cfg'])
print(["[INFO] loading Yolo..."])


net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)


if config.USE_GPU:
    print("[INFO] setting preferable backend and target to CUDA...")
    
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)


ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]


print("[INFO] accessing video stream... ")

vs = cv2.VideoCapture(args["input"] if args['input'] else 0)
writer = None

while True:
    grabbed, frame = vs.read()
    
    if not grabbed:
        break
        
    frame = cv2.resize(frame, (400,300))
    results = detect_poeple(frame, net, ln, personIndx=labels.index('person'))
    
    violate = set()
    
    if len(results) >= 2:
        centroids = np.array([r[2] for r in results])
        D = dist.cdist(centroids, centroids, metric='euclidean')
        
        for i in range(0, D.shape[0]):
            for j in range(i+1, D.shape[1]):
                if D[i, j] < config.MIN_DISTANCE:
                    violate.add(i)
                    violate.add(j)
                    
    for (i, (prob, bbox, centroid)) in enumerate(results):
        startX, startY, endX, endY = bbox
        cX, cY = centroid
        color = (0, 255, 0)
        
        if i in violate:
            color = (0,0,255)
            
        cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
        cv2.circle(frame, (cX, cY), 5, color, 1)
        
        text = "Social Distance Violations: {}".format(len(violate))
        
        cv2.putText(frame, text, (10, frame.shape[0]-25), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0,0,255), 3)
        
    if args['display'] > 0:
        cv2.imshow('Frame', frame)
        key = cv2.waitKey(10) & 0xFF
        
        if key == ord('q'):
            break
            
    if writer is not None:
        writer.write(frame)














