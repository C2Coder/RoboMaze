import * as gpio from "gpio";
import * as robomaze from "./libs/robomaze.js"

robomaze.begin(8); // sets up radio with group 8

robomaze.send("setname C2C") // sets your name/identifier to "something"

robomaze.send("join") // join a server (default is Robo) 

let button = 18;

gpio.pinMode(button, gpio.PinMode.INPUT_PULLUP);

gpio.on("falling", button, ()=>{
    robomaze.send("move up");  // sends the command over radio
})