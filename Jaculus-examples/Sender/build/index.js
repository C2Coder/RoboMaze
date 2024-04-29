import * as gpio from "gpio";
import * as robomaze from "./libs/robomaze.js";
let message_id = 10;
let last_message_id = message_id;
const nickname = "C2C";
const join_button = 18;
const forward_button = 16;
const right_button = 42;
gpio.pinMode(join_button, gpio.PinMode.INPUT_PULLUP);
gpio.pinMode(forward_button, gpio.PinMode.INPUT_PULLUP);
gpio.pinMode(right_button, gpio.PinMode.INPUT_PULLUP);
function recieve(_msg_id, _string) {
    let _data = _string.split("_");
    if (_data[0] != nickname) {
        console.log("msg not for me");
        return;
    }
    let data = _data[1].split("");
    let left = data[0]; //  \
    let forward = data[1]; //  | "1" or "0" if wall is in the direction or not
    let right = data[2]; //  /
    let dir = data[3]; // 0 - 3 (up, right, down, left) - what direction i am facing 
    let collected = data[4]; // "1" or "0" if collected a point
    console.log(`left:${left} fwd:${forward} right:${right} dir:${dir} point:${collected}`);
}
robomaze.create_cb(recieve);
robomaze.begin(8); // sets up radio with group 8
robomaze.send(`setname ${nickname}`, message_id); // sets your name/identifier to "something"
gpio.on("falling", join_button, () => {
    last_message_id = message_id;
    robomaze.send("join Robo", message_id); // join a server (if you dont specify a server you join a server with your name) 
    message_id++;
});
gpio.on("falling", forward_button, () => {
    last_message_id = message_id;
    robomaze.send("move forward", message_id); // sends the command over radio
    message_id++;
});
gpio.on("falling", right_button, () => {
    last_message_id = message_id;
    robomaze.send("rotate right", message_id); // sends the command over radio
    message_id++;
});
