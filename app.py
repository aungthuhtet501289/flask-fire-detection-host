import statistics
import time
import cv2
import base64
import numpy as np
import firebase_admin
from firebase_admin import credentials, db
from PIL import Image
from io import BytesIO
import torch
from tensorflow import keras
import tensorflow as tf
from tensorflow.keras.models import load_model

cred = credentials.Certificate('firedetection.json')
firebase_admin.initialize_app(cred, {'databaseURL': 'https://esp32cam-e5ea8-default-rtdb.asia-southeast1.firebasedatabase.app/'})
# Load the saved model
model = load_model("C:/Users/user/Desktop/fire and Web/fireprotectionand Web/better_fire_detection_model.h5") 
class imm():
    imgList=[]
def preprocessing_base64_image(base64_string):
    # Decode base64 string to bytes
    image_bytes = base64.b64decode(base64_string)
    # Convert bytes to image
    img = Image.open(BytesIO(image_bytes))
    # Convert image to array
    img_array = np.array(img)
    # Convert color format if needed (e.g., from RGBA to RGB)
    if img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    # Resize image
    img_array = cv2.resize(img_array, (196, 196))
    # Scale pixel values
    img_array = img_array / 255.0
    return img_array

from flask import *
app=Flask(__name__)

@app.route('/')
def index():
    fire_status=''
    # Fetch image data from Firebase
    ref = db.reference('/Images').get()
    img_data = ref['imageData']
    return render_template('index.html',original_img=img_data)

@app.route('/getSensorData', methods=['GET'])
def getSensorData():
    # Get sensor data from Firebase
    flame = db.reference('/SensorValue/flame').get()
    print(flame)
    gas = db.reference('/SensorValue/gas').get()
    temp = db.reference('/SensorValue/temperature').get()
    humidity = db.reference('/SensorValue/humidity').get()
    
    # Check if any data is missing
    if flame is None or temp is None or humidity is None:
        return jsonify(error="Failed to retrieve sensor data")
    
    # Return the sensor data if all values are available
    return jsonify(flame=flame, temp=temp, humidity=humidity,gas=gas)


@app.route('/getDecision', methods=['GET'])
def getDecision():
    flameList=[]
    tempList=[]
    humidityList=[]
    gasList=[]
    fire_cnnList=[]
    # fire_cvList=[]
    fire_status_cnn=''
    # fire_status_cv=''
    fire_decision=''
    for i in range(10):
        flame =db.reference('/SensorValue/flame').get()
        flameList.append(flame)
        gas =db.reference('/SensorValue/gas').get()
        gasList.append(gas)
        temp =db.reference('/SensorValue/temperature').get()
        tempList.append(temp)
        humidity =db.reference('/SensorValue/humidity').get()
        humidityList.append(humidity)
        ref = db.reference('/Images').get()
        
        # Fetch base64 image data from Firebase
        base64_image_data = ref['imageData']
        preprocessed_image = preprocessing_base64_image(base64_image_data)

        # Predict using the loaded model
        prediction = model.predict(np.expand_dims(preprocessed_image, axis=0))
        print(prediction)
        # Convert prediction to readable format
        if prediction[0][0] > 0.6:
            fire_status_cnn = 'Fire Detected'
            fire_cnnList.append(fire_status_cnn)
        else:
            fire_status_cnn = 'No Fire Detected'
            fire_cnnList.append(fire_status_cnn)
        time.sleep(1)
    flame_max=max(flameList)
    gas_max=max(gasList)
    humidity_max=max(humidityList)
    temp_max=max(tempList)
    fire_cnn_mdoe=statistics.mode(fire_cnnList)
    # fire_cv_mode=statistics.mode(fire_cvList)
    print(f'Flame Mean  {flame_max}' )
    print(f'Gas Mean  {gas_max}')
    print(f'Humidity Mean  {humidity_max}')
    print(f'Temp Mean  {temp_max}')
    print(f'FireCNN Mode  {fire_cnn_mdoe}')
    # print(f'FireCV Mode  {fire_cv_mode}')
    # if temp_max >30:
    #     print('true')

    if temp_max < 30 and gas_max < 35 and flame_max < 20 and fire_cnn_mdoe == 'No Fire Detected':
        fire_decision = 'Normal'
        send_actuators_data(fire_decision)
    elif 27 <= temp_max <= 40 and gas_max > 35 and 20 <= flame_max < 60 and (fire_cnn_mdoe == 'Fire Detected' or fire_cnn_mdoe == 'No Fire Detected'):
        fire_decision = 'Potential Fire'
        send_actuators_data(fire_decision)
    elif temp_max > 40 and gas_max > 35 and flame_max > 50 and fire_cnn_mdoe == 'Fire Detected':
        fire_decision = 'Fire'
        send_actuators_data(fire_decision)
    else:
        fire_decision = 'Normal'
        send_actuators_data(fire_decision)
    return jsonify({'flame_max':flame_max,'gas_max':gas_max,'humidity_max':humidity_max,'temp_max':temp_max,'fire_cnn_mdoe':fire_cnn_mdoe,'fire_decision':fire_decision})

def send_actuators_data(fire_decision):
    actuator_ref = db.reference('/Actuators')
    print('------------------------------------------------------------')
    print(fire_decision)
    if fire_decision == 'Normal':
        print('nnormal')
        actuator_ref.update({'buzzer': 'False', 'motor': 'False'})
    elif fire_decision == 'Potential Fire':
        print('potential')
        actuator_ref.update({'buzzer': 'True', 'motor': 'False'})
    elif fire_decision == 'Fire':
        print('fire')
        actuator_ref.update({'motor': 'True', 'buzzer': 'False'})
    else:
        print('else')
        actuator_ref.update({'buzzer': 'False', 'motor': 'False'})
    print('Successfully Updated!')

@app.route('/userCommand',methods=['POST'])
def userCommand():
    actuator_ref = db.reference('/Actuators')
    command=request.form.get('command')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print(command)
    actuator_ref.update({'motor': command, 'buzzer': 'False'})
    return jsonify({'message':'Successfully update!'})
# Fire detection with CNN
@app.route('/getData', methods=['GET'])
def get_data():
    ref = db.reference('/Images').get()
    fire_status_cnn=''
    base64_image_data = ref['imageData']
    preprocessed_image = preprocessing_base64_image(base64_image_data)
    # Predict using the loaded model
    prediction = model.predict(np.expand_dims(preprocessed_image, axis=0))
    print(prediction)
    # Convert prediction to readable format
    if prediction[0][0] > 0.6:
        fire_status_cnn = 'Fire Detected'
    else:
        fire_status_cnn = 'No Fire Detected'
    
    # Return the prediction result as a response
    return jsonify({'fire_status_cnn': fire_status_cnn,'original_img':base64_image_data})

if __name__ =='__main__':
    app.run(debug=True,host='0.0.0.0')