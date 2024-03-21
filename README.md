# RoboMaze 

## WORK IN PROGRESS - every .py file except Headless.py and server.py dont work :)

## Co to umí
Podpora více hráčů v týmech
Více serverů a světů 

## Servery a světy

V každém serveru může být jeden, nebo více světů

## Cestování mezi světy

Posbírejte barevné klíče, pomocí nich si můžete otevřít barevné dveře a to vám umožní cestovat mezi světy


## How to use # OUTDATED
- Git clone the repo
`git clone https://github.com/C2Coder/RoboMaze`

- Open the downloaded folder

- Install requirements 
`pip install -r requirements.txt`

- Run the app 
    - `python3 RoboMaze.py <user> <port> <Jaculus or Normal> <no-post (optional)>`
    - if you have a board with Jaculus connected 
    `python3 RoboMaze.py <user> <port> Jaculus` and put the port that your elks is connected, on windows something like COM26
    - if you have something else, like microbit connected
    `python3 RoboMaze.py <user> <port> Normal`
    - if you don't want to send data to server `python3 RoboMaze.py <port> Jaculus no-post`
- Run the server
    - if you want to play with more clients, use the server
    - `cd Server && python3 server.py` and it will print out on what port it is running, if you open that address in your browser and click **Start** you will see the plane and the avaliable colors

- If something doesnt work, send me a message on discord [@C2Coder](https://discord.com/users/612979947899846656 "My discord profile")


## Screenshots
- will update
![RoboMaze app](/screenshots/RoboMaze_app.png)