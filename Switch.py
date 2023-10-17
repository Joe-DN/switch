#-s 0x0017880109a56607 -b 0x001788010b1d1555
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

        self._shutdownHandler = ProcessShutdown()        
        self.__lwtTopic = f"test/status"           
        super().__init__()
       
    def on_message(self, mqttc, obj, msg): 
        data = json.loads(msg.payload.decode("UTF-8"))
        action = data["action"]

        if action == "on_press_release":
            self.publish(f"zigbee2mqtt/{self.__bulbId }/set",'{"state": "TOGGLE"}')
            logging.info(f"Toggle status for {self.__bulbId}")


 
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

