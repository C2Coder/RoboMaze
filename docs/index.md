# RoboMaze

[ukázkový projekt](../robomaze/robomaze_project.zip) i s knihovnou

## Příkazy

- `setname [jméno]` - nastav si jméno / přezdívku  
    - `setname C2C`
- `join [server]` - připoj se na server, pokud nedefinuješ server, připojíš se na server s tvým jménem
    - `join Robo`
    - `join` = `join C2C`

- `leave` - odpoj se ze serveru

- `move` - posuň se po mapě (dopředu/dozadu)
    - `move forward`
    - `move backward`
- `rotate` - otoč se (o 90° doleva/doprava)
    - `rotate left`
    - `rotate right`

## Jak hrát

1. Stáhni si ukázkový projekt i s knihovnou

2. Změn si jméno (pokud nechceš, nech prázdné)
    ```ts
    robomaze.send("setname [Jméno]") 
    ```

3. Připoj se k serveru (když nezadáš žádný, připojíš se k serveru s tvým jménem)
    ```ts
    robomaze.send("join")
    // nebo
    robomaze.send("join [Server]") 
    ```

4. Pohybuj se po mapě
    ```ts
    robomaze.send("move up")
    // nebo
    robomaze.send("move down")
    // nebo
    robomaze.send("move left")
    // nebo
    robomaze.send("move right")
    ```

## Cíl hry

- Posbírej co nejvíce bodů ￫ <span style="color:#D0A000">◼</span>

## Gamemody #TODO

1. Jeden svět na serveru, který se postupně zvětšuje s pozbíranými body

2. Je více světů a mezi nimi se můžete pohybovat pomocí dveří, které jsou ze začátku zavřené. Otevřete je pomocí nazbíraných klíčů. # TODO

## Barvy
- Body \
<span style="color:#D0A000">◼</span>

- Hráči \
<span style="color:#ffff50">◼</span> 
<span style="color:#99ff00">◼</span> 
<span style="color:#00ff99">◼</span> 
<span style="color:#00ffff">◼</span> 
<span style="color:#0099ff">◼</span> 
<span style="color:#3300ff">◼</span> 
<span style="color:#9900ff">◼</span> 
<span style="color:#ff00ff">◼</span>
<span style="color:#ff0099">◼</span>
<span style="color:#ff3300">◼</span>
<span style="color:#ff6600">◼</span>

- Klíče \
<span style="color:#ff0000">◼</span> 
<span style="color:#00ff00">◼</span> 
<span style="color:#0000ff">◼</span> 











## Kód pro BOARD

BOARD po stisknutí tlačítka pošle paint příkaz do počítače pomocí jacserial knihovny.

```ts
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
```
