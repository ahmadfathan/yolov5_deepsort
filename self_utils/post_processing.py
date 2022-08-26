import cv2,random,os,natsort,torch
import numpy as np
from skimage import draw

from pytorch_yolov5.utils.utils import scale_coords,plot_one_box

        
def detect_post_processing(np_img,pred,class_names,inference_shape,cameArea,class_colors=None):
    colors = class_colors if class_colors != None else [[random.randint(0, 255) for _ in range(3)] for _ in range(len(class_names))]
    if pred is not None and len(pred):
        pred[:, :4] = scale_coords(inference_shape[2:], pred[:, :4], np_img.shape).round()
        for *xyxy, conf, cls in pred:
            if cameArea.area_restrict and (not cameArea.box_in_area(xyxy)):
                continue
            text_info = '%s,%.2f' % (class_names[int(cls)],conf)
            plot_one_box(xyxy, np_img, text_info=text_info, color=colors[int(cls)]) 

    if cameArea.area_restrict:
        cameArea.draw_bounding(np_img)
    return np_img

def bbox_rel(image_width, image_height,  *xyxy):
    """" Calculates the relative bounding box from absolute pixel values. """
    bbox_left = min([xyxy[0].item(), xyxy[2].item()])
    bbox_top = min([xyxy[1].item(), xyxy[3].item()])
    bbox_w = abs(xyxy[0].item() - xyxy[2].item())
    bbox_h = abs(xyxy[1].item() - xyxy[3].item())
    x_c = (bbox_left + bbox_w / 2)
    y_c = (bbox_top + bbox_h / 2)
    w = bbox_w
    h = bbox_h
    return x_c, y_c, w, h

def deepsort_update(Tracker,pred,inference_shape,np_img):
    pred[:, :4] = scale_coords(inference_shape[2:], pred[:, :4], np_img.shape).round()
    bbox_xywh = []
    confs = []
    labels = []
    for *xyxy, conf, cls in pred:
        img_h, img_w, _ = np_img.shape
        x_c, y_c, bbox_w, bbox_h = bbox_rel(img_w, img_h, *xyxy)
        obj = [x_c, y_c, bbox_w, bbox_h]
        bbox_xywh.append(obj)
        confs.append([conf.item()])
        labels.append(int(cls))
    xywhs = torch.Tensor(bbox_xywh)
    confss = torch.Tensor(confs)
    outputs = Tracker.update(xywhs, confss , labels, np_img)
    return outputs

def track_post_processing(np_img,pred,class_names,inference_shape,cameArea,Tracker,class_colors=None):
    colors = class_colors if class_colors != None else [[random.randint(0, 255) for _ in range(3)] for _ in range(len(class_names))]
    if pred is not None and len(pred):
        outputs=deepsort_update(Tracker,pred,inference_shape,np_img)
        if len(outputs) > 0:
            bbox_xyxy = outputs[:, :4]
            labels = outputs[:, 4]
            identities = outputs[:, 5]
            Vx = outputs[:, 6]
            Vy = outputs[:, 7]
            for i in range(len(outputs)):
                box=bbox_xyxy[i]
                trackid=identities[i]
                label=labels[i]
                velocity=[Vx[i],Vy[i]]
                if cameArea.area_restrict and (not cameArea.box_in_area(box)):
                    continue
                text_info = '%s,ID:%d' % (class_names[int(label)],int(trackid))
                plot_one_box(box, np_img, text_info=text_info, velocity=velocity, color=colors[int(label)]) 

    if cameArea.area_restrict:
        cameArea.draw_bounding(np_img)
    return np_img

def dense_post_processing(np_img,pred,class_names,inference_shape,cameArea,class_colors=None):
    colors = class_colors if class_colors != None else [[random.randint(0, 255) for _ in range(3)] for _ in range(len(class_names))]
    if pred is not None and len(pred):
        pred[:, :4] = scale_coords(inference_shape[2:], pred[:, :4], np_img.shape).round()
        for *xyxy, conf, cls in pred:
            if cameArea.area_restrict and (not cameArea.box_in_area(xyxy)):
                continue
            text_info = '%s,%.2f' % (class_names[int(cls)],conf)
            plot_one_box(xyxy, np_img, text_info=text_info, color=colors[int(cls)]) 
    np_img=draw_obj_dense(np_img,pred[:, :4])
    if cameArea.area_restrict:
        cameArea.draw_bounding(np_img)
    return np_img

def count_post_processing(np_img,pred,class_names,inference_shape,theLine,Tracker,Obj_Counter,class_colors=None):
    colors = class_colors if class_colors != None else [[random.randint(0, 255) for _ in range(3)] for _ in range(len(class_names))]
    onTarget=False
    if pred is not None and len(pred):
        outputs=deepsort_update(Tracker,pred,inference_shape,np_img)
        if len(outputs) > 0:
            bbox_xyxy = outputs[:, :4]
            labels = outputs[:, 4]
            identities = outputs[:, 5]
            Vx = outputs[:, 6]
            Vy = outputs[:, 7]
            for i in range(len(outputs)):
                box=bbox_xyxy[i]
                trackid=identities[i]
                label=labels[i]
                velocity=[0-Vy[i],Vx[i]]
                if theLine.box_on_line(box):
                    onTarget=True
                    Obj_Counter.counter_update(class_names[int(label)],trackid,velocity,theLine.positive_direction,theLine.negetive_direction)
                text_info = '%s,ID:%d' % (class_names[int(label)],int(trackid))
                plot_one_box(box, np_img, text_info=text_info, color=colors[int(label)]) 

    np_img=theLine.draw_line(np_img,onTarget)
    np_img=Obj_Counter.draw_counter(np_img)
    return np_img

def field_post_processing(np_img,pred,class_names,inference_shape,Field,Tracker,class_colors=None):
    colors = class_colors if class_colors != None else [[random.randint(0, 255) for _ in range(3)] for _ in range(len(class_names))]
    if pred is not None and len(pred):
        outputs=deepsort_update(Tracker,pred,inference_shape,np_img)
        if len(outputs) > 0:
            bbox_xyxy = outputs[:, :4]
            labels = outputs[:, 4]
            identities = outputs[:, 5]
            Vx = outputs[:, 6]
            Vy = outputs[:, 7]
            for i in range(len(outputs)):
                box=bbox_xyxy[i]
                trackid=identities[i]
                label=labels[i]
                velocity=[Vx[i],Vy[i]]
                text_info = '%s,ID:%d' % (class_names[int(label)],int(trackid))
                flag=Field.update(box,velocity)
                color=[0,200,0] if flag else [0,0,200]
                plot_one_box(box, np_img, text_info=text_info,velocity=velocity, color=color)
    np_img=Field.draw_vector_field(np_img)
    return np_img
                
def draw_obj_dense(img,box_list,k_size=281,beta=1.5):
    value=np.ones((img.shape[0],img.shape[1])).astype('uint8')
    value=value*10
    value=fill_box(box_list,value)
    value=cv2.GaussianBlur(value, ksize=(k_size,k_size),sigmaX=0,sigmaY=0)
    color=value_to_color(value)
    color=cv2.cvtColor(color,cv2.COLOR_RGB2BGR)
    value[value<=20]=0.9
    value[value>20]=1.0
    mask=np.ones_like(img)
    mask[:,:,0]=value
    mask[:,:,1]=value
    mask[:,:,2]=value
    mask_color=mask*color
    mask_color=cv2.GaussianBlur(mask_color, ksize=(7,7),sigmaX=0,sigmaY=0)
    result = cv2.addWeighted(img, 1, mask_color, beta, 0)
    info='Total number: {}'.format(len(box_list))
    W_size,H_size=cv2.getTextSize(info, cv2.FONT_HERSHEY_TRIPLEX, 0.8 , 2)[0]
    cv2.putText(result, info, (3, 1+H_size+9), cv2.FONT_HERSHEY_TRIPLEX, 0.8, [0,255,0], 2)
    return result

def between(x,x_min,x_max):
    return min(x_max,max(x,x_min))

def fill_box(box_list,mask,fill_size=25):
    for box in box_list:
        cenXY=[(box[0]+box[2])/2,(box[1]+box[3])/2]
        cenXY=[between(cenXY[0],0+fill_size,mask.shape[1]-fill_size),between(cenXY[1],0+fill_size,mask.shape[0]-fill_size)]
        Y=np.array([cenXY[1]-fill_size,cenXY[1]-fill_size,cenXY[1]+fill_size,cenXY[1]+fill_size])
        X=np.array([cenXY[0]-fill_size,cenXY[0]+fill_size,cenXY[0]+fill_size,cenXY[0]-fill_size])
        yy, xx=draw.polygon(Y,X)
        mask[yy, xx] = 255
    return mask

def value_to_color(grayimg,low_value=15,high_value=220,low_color=[10,10,10],high_color=[255,10,10]):
    r=low_color[0]+((grayimg-low_value)/(high_value-low_value))*(high_color[0]-low_color[0])
    g=low_color[1]+((grayimg-low_value)/(high_value-low_value))*(high_color[1]-low_color[1])
    b=low_color[2]+((grayimg-low_value)/(high_value-low_value))*(high_color[2]-low_color[2])
    rgb=np.ones((grayimg.shape[0],grayimg.shape[1],3))
    rgb[:,:,0]=r
    rgb[:,:,1]=g
    rgb[:,:,2]=b
    return rgb.astype('uint8')
