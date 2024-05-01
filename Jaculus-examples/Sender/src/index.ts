import * as gpio from "gpio";
import * as robomaze from "./libs/robomaze.js"

let message_id = 10;
let last_message_id = message_id;

const nickname = "C2C"
const join_button = 18;
const forward_button = 16;
const right_button = 42;

gpio.pinMode(join_button, gpio.PinMode.INPUT_PULLUP);
gpio.pinMode(forward_button, gpio.PinMode.INPUT_PULLUP);
gpio.pinMode(right_button, gpio.PinMode.INPUT_PULLUP);

function recieve(_msg_id: number, _string: string) {
    console.log("recieved")
    for (let i = 0; i < _string.length; i++) {
        console.log(_string.charCodeAt(i));
    }

    //         8     1     1   1      1         1        1       1      1     1      = 17/22
    // <id> <nick> <size> <x> <y> <x_point> <y_point> <x_key> <y_key> <dir> <sens>

    // Player nick
    const nick = _string.substring(0, 8)

    // Maze/world size
    const size:Number = _string.charCodeAt(8)

    // Player pos
    const x:Number = _string.charCodeAt(9)
    const y:Number = _string.charCodeAt(10)

    // Nearest point pos
    const x_point:Number = _string.charCodeAt(11)
    const y_point:Number = _string.charCodeAt(12)

    // Nearest key pos
    const x_key:Number = _string.charCodeAt(13)
    const y_key:Number = _string.charCodeAt(14)

    // Player dir
    const dir:Number = _string.charCodeAt(15) - 1

    // Sensors
    const [left, back, right, fwd] = (_string.charCodeAt(16) - 1).toString(2).padEnd(4, "0").split('');

}
robomaze.begin(8); // sets up radio with group 8

robomaze.create_cb(recieve);

robomaze.send(`setname ${nickname}`, message_id) // sets your name/identifier to "something"

gpio.on("falling", join_button, () => {
    last_message_id = message_id
    robomaze.send("join Robo", message_id) // join a server (if you dont specify a server you join a server with your name) 
    message_id++;
})

gpio.on("falling", forward_button, () => {
    last_message_id = message_id
    robomaze.send("move forward", message_id);  // sends the command over radio
    message_id++;
})

gpio.on("falling", right_button, () => {
    last_message_id = message_id
    robomaze.send("rotate right", message_id);  // sends the command over radio
    message_id++;
})