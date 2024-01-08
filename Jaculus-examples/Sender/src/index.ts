import * as gpio from "gpio";
import * as RM from "./libs/robomaze.js"

RM.begin(8); // sets up radio with group 8
RM.set_name("ELKS"); // sets the name/identifier so the commands are "ELKS move up"


console.log(RM.name);
gpio.pinMode(18, gpio.PinMode.INPUT_PULLUP);
gpio.pinMode(16, gpio.PinMode.INPUT_PULLUP);


gpio.on("falling", 18, ()=>{
    RM.send_serial("move up"); // sends the command over serial
    RM.send_radio("move up");  // sends the command over radio
})

gpio.on("falling", 16, ()=>{
    RM.send_serial("move down"); // sends the command over serial
    RM.send_radio("move down");  // sends the command over radio
})
