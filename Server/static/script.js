server_ip = '10.0.1.30'
port = 8000
ws_port = 8001

raw_pixels = "";

maze_id = "Robo" // default id

size = 1 // default walue
pixel_size = 10 // default value

colors = [
  "#ffff00",
"#ccff00",
"#99ff00",
"#66ff00",
"#33ff00",
"#00ff00",
"#00ff33",
"#00ff66",
"#00ff99",
"#00ffcc",
"#00ffff",
"#00ccff",
"#0099ff",
"#0066ff",
"#0033ff",
"#0000ff",
"#3300ff",
"#6600ff",
"#9900ff",
"#cc00ff",
"#ff00ff",
"#ff00cc",
"#ff0099",
"#ff0066",
"#ff0033",
"#ff0000",
"#ff3300",
"#ff6600",
"#EEBB00",
"#222222",
"#FFFFFF",
];

chars = [
  "a",
"b",
"c",
"d",
"e",
"f",
"g",
"h",
"i",
"j",
"k",
"l",
"m",
"n",
"o",
"p",
"q",
"r",
"s",
"t",
"u",
"v",
"w",
"x",
"y",
"z",
"A",
"B",
"K",
"L",
"M",
];

async function start() {
  maze_id = document.getElementById("mazeID").value
  //console.log(maze_id)
  
  document.getElementById("mazeID").remove()
  document.getElementById("mazeID_label").remove()
  document.getElementById("start_button").remove();

  var display_div = document.createElement("div");
  display_div.id = "display";
  document.body.appendChild(display_div);

  
  var canvas = document.createElement("canvas");
  canvas.id = "canvas";
  
  display_div.appendChild(canvas);
  
  picture = document.createElement("img");
  picture.src = "static/colors.png";
  document.body.appendChild(picture);
  
  await get_size();
  set_size();
  update();
}

function set_size(){
  var canvas = document.getElementById("canvas")
  pixel_size = 100
  canvas.width = size * pixel_size;
  canvas.height = size * pixel_size;
}

async function sendMessageAndAwaitResponse(messageToSend) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket("ws://" + server_ip + ":" + ws_port);
    
    socket.onopen = () => {
      socket.send(messageToSend);
    };
    
    socket.onmessage = (event) => {
      resolve(event.data);
      socket.close(); // Close the connection after receiving the response
    };
    
    socket.onerror = (error) => {
      reject(error);
    };
  });
}

async function get_size(){
  try {
    const response = await sendMessageAndAwaitResponse(`get_size ${maze_id}`);
    size = response.replace("size:", "")
    //console.log(size)
  } catch (error) {
    console.error('Error occurred:', error);
  }
}

async function get_pixels(){
  try {
    const response = await sendMessageAndAwaitResponse(`get_pixels ${maze_id}`);
    raw_pixels = response.replace("data:", "")
    //console.log(size)
  } catch (error) {
    console.error('Error occurred:', error);
  }
}


function draw_on_display(raw_pixels) {
  var c = document.getElementById("canvas");
  var ctx = c.getContext("2d");

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      ctx.fillStyle = colors[chars.indexOf(raw_pixels[y * size + x])];
      ctx.fillRect(x * pixel_size, y * pixel_size, pixel_size, pixel_size);
      ctx.stroke();
    }
  }
}

async function update() {
  
  await get_size()
  await get_pixels()
  set_size();
  draw_on_display(raw_pixels)

  setTimeout(update, 1000);
}
