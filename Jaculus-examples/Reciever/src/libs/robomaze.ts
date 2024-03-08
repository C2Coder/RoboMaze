/**
* A lib for sending data to robomaze (https://github.com/C2Coder/RoboMaze)
*/

import * as radio from "simpleradio"

export function create_callback() {
    radio.on("string", (str, info) => {
        send_serial_raw(str, info.address)
    })
}

export function send_serial(_cmd: string) {
    console.log(`|serial ${_cmd}|`)
}

function send_serial_raw(_string: string, _addr:string) {
    console.log(`|${_addr} ${_string}|`)
}

export function begin(_group: number) {
    radio.begin(_group);
}

export function send_radio(_cmd: string) {
    radio.sendString(`${_cmd} ${Math.round(Math.random() * 1000)}`)
}