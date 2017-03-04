/*
 *  Customized script from original WiFiClient example from sparkfun.com
 *
 */

#include <ESP8266WiFi.h>

// insert your WIFI SSID and PSK
const char WiFiSSID[] = "xxx" ;
const char WiFiPSK[] = "yyy";


const int RIGHT =5; 
const int LEFT = 2; 
const int UP = 14; 
const int DOWN = 0; 
const int BUT1 = 16; 
const int BUT2 = 12; 
const int BUT3 = 13; 
const int BUT4 = 4;

//insert RaspiPi IP adress
const char HOST[] = "xxx.xxx.xxx.xxx";


void setup() {
  Serial.begin(115200);
  delay(100);
  pinMode(RIGHT,INPUT_PULLUP);
  pinMode(LEFT,INPUT_PULLUP);
  pinMode(UP,INPUT_PULLUP);
  pinMode(DOWN,INPUT_PULLUP);
  pinMode(BUT1,INPUT);
  pinMode(BUT2,INPUT_PULLUP);
  pinMode(BUT3,INPUT_PULLUP);
  pinMode(BUT4,INPUT_PULLUP);
  
  // We start by connecting to a WiFi network
  
  WiFi.begin(WiFiSSID, WiFiPSK);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");  
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

int value = 0;

void loop() {
  delay(5000);
  ++value;

  Serial.print("connecting to ");
  Serial.println(HOST);
  
  // Use WiFiClient class to create TCP connections
  WiFiClient client;
  const int Port = 4711;
  if (!client.connect(HOST, Port)) {
    Serial.println("connection failed");
    return;
  }
  byte message = 0x00;
  byte oldmessage = 0x80;
  while(true)
  {
   
    
    message = 0x00;
    if (!digitalRead(LEFT)) bitSet(message,0);
    if (!digitalRead(RIGHT)) bitSet(message,1);
    if (!digitalRead(UP)) bitSet(message,2);
    if (!digitalRead(DOWN)) bitSet(message,3);
    if (!digitalRead(BUT1)) bitSet(message,4);
    if (!digitalRead(BUT2)) bitSet(message,5);
    if (!digitalRead(BUT3)) bitSet(message,6);
    if (!digitalRead(BUT4)) bitSet(message,7);

    if (oldmessage != message)
    {
      uint8_t * sbuf = (uint8_t *)malloc(1);
      sbuf[0]=message;
      client.write((uint8_t *)sbuf, 1);
      yield();
      //Serial.write(message);
      free(sbuf);
      oldmessage = message;
    }
     else
     {
      delay(5);
     }
     
   
  }
  
  Serial.println();
  Serial.println("closing connection");
}

