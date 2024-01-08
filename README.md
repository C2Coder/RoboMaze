# RoboPlace

## Library for Jaculus
- Custom library is in the example projects included in this project
- Sender example - a simple example that sends paint commands on the push of a button
- Reciever example - a simple example that send commands which it recieves from radio

## How to use
- Git clone the repo
`git clone https://github.com/C2Coder/RoboPlace`

- Open the downloaded folder

- Install requirements 
`pip install -r requirements.txt`

- Run the app 
    - `python3 RoboPlace.py <port> <Jaculus or Normal> <no-post (optional)>`
    - if you have a board with Jaculus connected 
    `python3 RoboPlace.py <port> Jaculus` and put the port that your elks is connected, on windows something like COM26
    - if you have something else, like microbit connected
    `python3 RoboPlace.py <port> Normal`
    - if you don't want to send data to server `python3 RoboPlace.py <port> Jaculus no-post`
- Run the server
    - if you want to play with more clients, use the server
    - `cd Server && python3 server.py` and it will print out on what port it is running, if you open that address in your browser and click **Start** you will see the plane and the avaliable colors

- If something doesnt work, send me a message on discord [@C2Coder](https://discord.com/users/612979947899846656 "My discord profile")

