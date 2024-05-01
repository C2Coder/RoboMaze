import { readline } from "./libs/readline.js";
import * as radio from "simpleradio";
radio.begin(8);
radio.on("string", (str, info) => {
    console.log(`${info.address} ${str}`);
});
async function serial_reader() {
    const reader = new readline(true); // true -> echo
    while (true) {
        const line = await reader.read();
        //         8     1     1   1      1         1        1       1      1     1      = 17/22
        // <id> <nick> <size> <x> <y> <x_point> <y_point> <x_key> <y_key> <dir> <sens>
        const toks = line.replace("\n", "").split(" ");
        let s = "";
        s += toks[1].padEnd(8); // nick
        for (let i = 2; i < 11; i++) {
            s += String.fromCharCode(Number(toks[i]));
        }
        radio.sendKeyValue(s, Number(toks[0]));
    }
}
serial_reader();
