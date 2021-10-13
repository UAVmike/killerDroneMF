import datetime
import math
import sys
import cv2
import numpy as np
from vidstab import VidStab

'''
removed unused tracker types
put trackbar in main window
put a target in the center of the screen
calculated how many times the center of the track box hit the center of the screen
'''

#define a function for the trackbar
def nothing(x):
    pass
#create a global varrient for the tracker type so we can use it in functions
global tracker_type,modulation

#create windows so we can use them 
cv2.namedWindow('Tracking')
cv2.createTrackbar('size','Tracking',0,3,nothing)

#vidstab command for defining stabilizationg method
stabilizer=VidStab(kp_method='ORB')


#creating function that handles mouse events
def mouse_drawing(event,x,y,flags,params):
    #defining global varrients for the function to use each time a mouse event occurs 
    global initbb, tracker
    #when user clicks left mouse button the program detects it and enters 
    if event==cv2.EVENT_LBUTTONDOWN:
        #creating the bounding box of the tracker based on the area the user has clicked
        initbb=(x-B_box_width,y-B_box_heith,x+B_box_width-(x-B_box_width),y+B_box_heith-(y-B_box_heith))
        #checking what tracker type we are using, based on the line in main function
        #and then creating it
        if tracker_type == 'KCF':
            tracker = cv2.TrackerKCF_create()
        if tracker_type == 'MEDIANFLOW':
            tracker = cv2.legacy.TrackerMedianFlow_create()
        if tracker_type == 'GOTURN':
            tracker = cv2.TrackerGOTURN_create()
        if tracker_type == 'MOSSE':
            tracker = cv2.TrackerMOSSE_create()
        if tracker_type == "CSRT":
            tracker = cv2.TrackerCSRT_create()
        #initialize tracking based on tracker type and bounding box
        tracker.init(frame,initbb)

#creating a function to recieve our camera feed information
def get_vid_info(video):
    w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH)) 
    h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fpscam=int(video.get(cv2.CAP_PROP_FPS)) 
    return w,h,fpscam 

#resize function in case our frame is too big
def resize(w,h,wmax,hmax):
    if w > Wmax or h > Hmax:
        ratio = 1280/w
        w = 1280
        h = int(h*ratio)
    return w, h

def initialize_modulation(modulation):
    def init_by_modulation(num):
        global B_box_width, B_box_heith, center_constant
        B_box_width=round(h/num)
        B_box_heith=round(w/num)
        center_constant[0]=round(w/num)
        center_constant[1]=round(h/num)
    if modulation==0:
        init_by_modulation(40)
    elif modulation==1:
        init_by_modulation(60)
    elif modulation==2:
        init_by_modulation(80)
    elif modulation==3:
        init_by_modulation(100)
    return B_box_width,B_box_heith,center_constant
  
def Draw_circle_center(center,center_constant,frame):
    cv2.circle(frame,(int(center[0]),int(center[1])),int(center_constant[0]),(0,0,255),2)
    cv2.line(frame,(int(center[0])-int((center_constant[0])),int(center[1])),(int(center[0])+int((center_constant[0])),int(center[1])),(255,0,0),1)
    cv2.line(frame,(int(center[0]),int(center[1])-int((center_constant[1]))),(int(center[0]),int(center[1])+int((center_constant[1]))),(255,0,0),1)  

def Draw_bounding_box(initbb,frame,ok):
    if ok:
        # Tracking success
        #print(initbb)
        p1 = (int(initbb[0]), int(initbb[1]))
        p2 = (int(initbb[0] + initbb[2]), int(initbb[1] + initbb[3]))
        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
    else:
        # Tracking failure
        initbb=initbb+(0,0,15,15)
        #initbb[3]=initbb[3]+5
        ok,initbb=tracker.update(frame)
        cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

def Draw_distance_vector(initbb,w,h):
    #calculating distance between target and box center
    dx=bbcenter[0]-w/2
    dy=bbcenter[1]-h/2
    #calculating normalization value
    u=int(math.sqrt(dx**2+dy**2))
    if u:
        dx=int(20*(dx/u))
        dy=int(20*(dy/u))
        #displaying the direction of the distance vector
        cv2.arrowedLine(frame,(w-50,50),(w-50+dx,50+dy), (0,0,255), 3)
    cv2.circle(frame,(w-50,50),20,(0,0,255),1)
            
def center_hits_counter(bbcenter,center_constant,m):
    global counter_hits
    #building a counter to how many times the tracker center has hit the target center
    #within a range of our choosing
    if (bbcenter[0])>=int(center[0]-center_constant[0]/2) and (bbcenter[0])<=int(center[0]+center_constant[0]/2) and (bbcenter[1])>=int(center[1]-center_constant[1]/2) and (bbcenter[1])<=int(center[1]+2*center_constant[1]):
        m=1
        counter_hits=counter_hits+1
        # print('fire'+str(counter_hits))
    if m==1:
        print(counter_hits)
    else:
        if counter_hits>0:
            print("stayed in frame for "+str(counter_hits)+" frames")
            frame_array.append(counter_hits)
        counter_hits=0
    # print(counter_hits)
    return frame_array
    
#openCV function that detects mouse events and sends the event to our function
cv2.setMouseCallback('Tracking',mouse_drawing)


if __name__ == '__main__':
    # initializing variable:
    n=0
    m=0
    # Set up tracker.
    initbb=None
    tracker_types = [ 'KCF', 'MEDIANFLOW', 'GOTURN', 'MOSSE', 'CSRT']
    tracker_type = tracker_types[4]
    
    # Read video and get its size and fps
    # video = cv2.VideoCapture('D:/IDF/DJI_0025.mp4')
    video = cv2.VideoCapture(0)
    w,h,fpscam=get_vid_info(video)       
    print(w,h,fpscam)
    
    # max height and width we want to see
    Wmax=1280
    Hmax=720
    w,h=resize(w,h,Wmax,Hmax)
    
    #and center of screen
    center=(w/2,h/2) 
    
    # config files:
    # counters for target hit center 
    counter_frame=0
    counter_hits=0
    frame_array=[]
    center_constant=[0,0]

    # Exit if video not opened.
    if not video.isOpened():
        print('Cannot read video file1')
        sys.exit()

    # Read first frame.
    ok, frame = video.read()
    if not ok:
        print('Cannot read video file2')
        sys.exit()

    #making a path to our file writer 
    # outvid=cv2.VideoWriter("D:/live_vid_dan.avi",cv2.VideoWriter_fourcc('F','M','P','4'),fps,(w,h))
    
    #creating track bar conditions
    modulation=cv2.getTrackbarPos('size','Tracking')
    #depending on track bar position we change the bounding box dimentions

    B_box_width,B_box_heith,center_constant=initialize_modulation(modulation)
    
    # put a mark on screen center
    Draw_circle_center(center,center_constant,frame)

    
    #initializing loop to start stream
    while video.isOpened():
        counter_frame=counter_frame+1
                
        #check time to calculate run time and fps
        before = datetime.datetime.now()

        # Read a new frame
        ok, frame = video.read()
        
        #resizing frame to fit the screen 
        frame=cv2.resize(frame,(int(w),int(h)))

        #check to see if we can read the frame
        if not ok:
            continue
        #initbb starts at 0 and only changes if we click to track, 
        #when we click initbb value changes and we enter the IF function
        if initbb:
            #initialize track bars again so we can repeat the tracking each time we 
            #want to change position or track bar value without needing to reset
            modulation=cv2.getTrackbarPos("size",'Tracking')

            B_box_width,B_box_heith,center_constant=initialize_modulation(modulation)

            # Start timer
            timer = cv2.getTickCount()

            # Update tracker
            ok, initbb = tracker.update(frame)

            # Calculate Frames per second (FPS)
            fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)

            # Draw bounding box
            Draw_bounding_box(initbb,frame,ok)
            
            # Display tracker type on frame
            cv2.putText(frame, tracker_type + " Tracker", (100, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2);
            # Display FPS on frame
            cv2.putText(frame, "FPS : " + str(int(fps)), (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2);

            #bounding box center coordinates
            bbcenter=(initbb[0]+int(initbb[3]/2),initbb[1]+int(initbb[3]/2))  
            #calculating and displaying the vector between tracker and target:    
            Draw_distance_vector(bbcenter,w,h)
            frame_array=center_hits_counter(bbcenter,center_constant,m)
            
        # Display result
        #building a target in the center of the screen to display it
        Draw_circle_center(center,center_constant,frame)
        
        #displaying video, and saving the results to file
        cv2.imshow("Tracking", frame)
        cv2.moveWindow("Tracking",0,0)
        # outvid.write(frame)
        #set the stabilizing, smoothing window will determine the delay and 
        #stabilizing quality 
        stabilized_frame=stabilizer.stabilize_frame(input_frame=frame,smoothing_window=5,border_size=80)
        cv2.imshow("stabilized",stabilized_frame)
        cv2.moveWindow("stabilized",800,0)
        #check delay between frames
        # print(datetime.datetime.now() - before)
        
        # Exit if q pressed, and pause of spacebar is pressed
        key=cv2.waitKey(1)
        if key==ord('q') & 0xff:
            break
        if key==32 & 0xff:
            cv2.waitKey()
        m=0
        
print(frame_array)
video.release()
# outvid.release()
cv2.destroyAllWindows()
