import { readline } from "./libs/readline.js";
import * as radio from "simpleradio"

radio.begin(8)

radio.on("string", (str, info) => {
    console.log(`${info.address} ${str}`)
})


async function serial_reader() {
    const reader = new readline(true); // true -> echo
    while (true) {
        const line = await reader.read();
        const toks = line.split(" ");
        radio.sendKeyValue(toks[1], Number(toks[0]));
    }
    
}

serial_reader()