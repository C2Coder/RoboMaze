/**
* A lib for sending data to robomaze (https://github.com/C2Coder/RoboMaze)
*/

import * as radio from "simpleradio"

export let name = "" // default name

export function create_callback() {
    radio.on("string", (str, info) => {
        send_serial_raw(str)
    })
}

export function send_serial(_cmd: string) {
    console.log(`|${name} ${_cmd}|`)
}
function send_serial_raw(_string: string) {
    console.log(`|${_string}|`)
}

export function set_name(_name: string) {
    name = _name.substring(0, 10);
}

export function begin(_group: number) {
    radio.begin(_group);
}

export function send_radio(_cmd: string) {
    radio.sendString(`${name} ${_cmd} ${Math.round(Math.random() * 1000)}`)
}