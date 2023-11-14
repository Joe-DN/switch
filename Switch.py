#-s 0x0017880109a56607 -b 0x001788010b1d1555 asdas
import json
import argparse
import signal
import logging
import paho.mqtt.client as mqtt

class ProcessShutdown:

  sc = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exitGracefully)
    signal.signal(signal.SIGTERM, self.exitGracefully)

  def exitGracefully(self, *args):
    self.sc = True

class Switch(mqtt.Client):

    def __init__(self, switchId, bulbId):                 
        self.__switchId = switchId
        self.__bulbId  = bulbId
        self.__brightness = 0
        self.__brightnessStep = 20

        self._shutdownHandler = ProcessShutdown()        
        self.__lwtTopic = f"test/status"           
        super().__init__()
       
    def on_message(self, mqttc, obj, msg): 
        data = json.loads(msg.payload.decode("UTF-8"))

        if(self.__switchId in msg.topic):
            action = data["action"]

            if action == "on_press_release":
                self.publish(f"zigbee2mqtt/{self.__bulbId }/set",'{"state": "TOGGLE"}')
                logging.info(f"On press for {self.__bulbId}")

            if action == "off_press_release":                
                logging.info(f"Off press for {self.__bulbId}")

            if action == "up_press_release":                
                self.increaseBrightnessValue()
                val = {}
                val["brightness"] = self.__brightness
                self.publish(f"zigbee2mqtt/{self.__bulbId }/set",json.dumps(val))
                #self.publish(f"zigbee2mqtt/{self.__bulbId }/set",'{"state": "TOGGLE"}')
                logging.info(f"Up press for {self.__bulbId}")

            if action == "down_press_release":
                self.decreaseBrightnessValue()
                val = {}
                val["brightness"] = self.__brightness
                self.publish(f"zigbee2mqtt/{self.__bulbId }/set",json.dumps(val))
                logging.info(f"Down press for {self.__bulbId}")
        
        if(self.__bulbId in msg.topic):
            self.__brightness = data["brightness"]
             
    def increaseBrightnessValue(self):
        self.__brightness += self.__brightnessStep

        if self.__brightness > 254:
            self.__brightness = 254
        
        if self.__brightness < 0:
            self.__brightness = 0

    def decreaseBrightnessValue(self):
        self.__brightness -= self.__brightnessStep

        if self.__brightness > 254:
            self.__brightness = 254
        
        if self.__brightness < 0:
            self.__brightness = 0

    def on_connect(self, mqttc, obj, flags, rc):
        self.publish(self.__lwtTopic,"2" , retain=True)  
        logging.info("Connection to MQTT broker successful")


    def connectToBroker(self):
        try:
            self.will_set(self.__lwtTopic,"0", retain=True)    
            self.connect("10.0.0.5",1883)
        except Exception as e:            
            logging.error(f'Failed to connect to broker')
            return -1

    def run(self):
        rc = 0        
        self.subscribe(f"zigbee2mqtt/{self.__switchId}",0)
        self.subscribe(f"zigbee2mqtt/{self.__bulbId}",0)
        self.publish(f"zigbee2mqtt/{self.__bulbId }/get",'{"brightness": ""}')
        while rc == 0:
            if(self._shutdownHandler.sc):
                return
            rc = self.loop()    
        return rc


def main():

    parser = argparse.ArgumentParser('file decryption deamon')
    parser.add_argument('-s', dest='switch', action='store', type=str, required=True)
    parser.add_argument('-b', dest='bulb', action='store', type=str, required=True )

    args = vars(parser.parse_args())

    mqttc = Switch(args["switch"],args["bulb"])

    try:
        mqttc.connectToBroker()
        rc = mqttc.run()
        if not rc == None:
            logging.error(f"Failed to connect to broker, code {str(rc)}")
                
        else:
            logging.info("Kill recevied, exiting")
    except KeyboardInterrupt as Exception:
        pass

if __name__ == "__main__":
    main() 

