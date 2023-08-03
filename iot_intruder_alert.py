import os, time, sys, json, requests as rqts
from boltiot import Bolt

# Bolt device Id and API key
device_id = os.environ.get('DEVICE_ID')
api_key = os.environ.get('API_KEY')
# Twilio account SID and authentication token
acc_sid = os.environ.get('SID')
auth_token = os.environ.get('AUTH_TOKEN')
# Twilio phone number(from_number) and recipient's phone number(to_number)
from_number = os.environ.get('FROM_NUMBER')
to_number = os.environ.get('TO_NUMBER')


# Initialize the Bolt object
my_bolt = Bolt(api_key, device_id)

def send_message_from_twilio(Body):
    '''Send sms to recipient's mobile number
    
    Parameter:
    Body (str): Message body 
    '''
    
    # Twilio API endpoint URL
    twilio_api_url = f'https://api.twilio.com/2010-04-01/Accounts/{acc_sid}/Messages.json'

    # Create the message data
    data = {
        'From': from_number,
        'To': to_number,
        'Body': Body
    }

    # Send the SMS message using the requests library
    response = rqts.post(twilio_api_url, data=data, auth=(acc_sid, auth_token)) 

    # Check the response status to verify if the message was sent successfully
    if response.status_code == 201:
        print('SMS sent successfully.')
    else:
        print('Error sending SMS:', response.text)

def check_device_status():
    '''Returns Ture if Device is online'''
    my_bolt = Bolt(api_key, device_id)
    device_response = my_bolt.isOnline()
    device_data = json.loads(device_response)
    return device_data['value'] == 'offline'

def check_led_status():
    '''Returns Ture if LED is on'''
    led_response = my_bolt.digitalRead('0')
    led_data = json.loads(led_response)
    if led_data['success'] == 0:
        print(led_data['value'])
        sys.exit()
    return led_data['value'] == '1'

def detect_sudden_change():
    '''Detect sudden heavy drop in voltage across LRD'''
    try: 
        ldr_response = my_bolt.analogRead('A0')
        ldr_data = json.loads(ldr_response)
        sensor_value = int(ldr_data['value']) 
        if abs(sensor_value) < 1024:
            print("Analog Reading detected below 1024")
            return True
        time.sleep(15)
    except Exception as e:
        print ("Error occured, below are the details:")
        print (e)

def start_buzzer():
    '''Turn On Buzzer for 20 seconds'''
    try:
        my_bolt.digitalWrite('1', 'HIGH')
        time.sleep(20)
        my_bolt.digitalWrite('1', 'LOW')
        print("Buzzer stoped after 20 seconds")
    except KeyboardInterrupt:
        my_bolt.digitalWrite('0', 'LOW')
        my_bolt.digitalWrite('1', 'LOW')
        print("KeyboardInterrupt: Stopping the script.")



try:
    while True:
        if check_led_status():
            print("LED is on. Starting Python code execution.")
            
            # If sudden change in light intensity detected, alert the house owner
            if detect_sudden_change():
                send_message_from_twilio("Possible intruders detected at your home. Take immediate action to safeguard your belongings.")
                start_buzzer()
                sys.exit()

        else:
            # Check device status
            if check_device_status():
                print("Your device is off")
            else:
                print("Your intruder detecting system is OFF. \nMake sure to turn it ON before leaving the house.")
                pass

        # Wait for a few seconds before checking again
        time.sleep(30)

except KeyboardInterrupt:
    my_bolt.digitalWrite('0', 'LOW')
    my_bolt.digitalWrite('1', 'LOW')
    print("KeyboardInterrupt: Stopping the script.")
