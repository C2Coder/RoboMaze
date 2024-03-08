server_ip = '10.0.1.30'
port = 8000
ws_port = 8001
proxy_addr = 'hotncold.ddns.net'
proxy_port = 8000
proxy_ws_port = 8001

raw_pixels = "";

user_id = "Robo"; // default id

size = 1; // default walue
pixel_size = 10; // default value

colors = {
  a: "#ffff50", // \
  b: "#99ff00", // |
  c: "#00ff99", // |
  d: "#0099ff", // |
  e: "#3300ff", // |  Used for Players
  f: "#9900ff", // |
  g: "#ff00ff", // |
  h: "#ff0099", // |
  i: "#ff3300", // |
  j: "#ff6600", // /

  A: "#ff0000", // \
  B: "#ffff00", // |
  C: "#00ff00", // |  Used for keys
  D: "#00ffff", // |
  E: "#0000ff", // /

  F: "#222222", // \
  G: "#440000", // |
  H: "#444400", // |  Used for walls
  I: "#004400", // |
  J: "#004444", // |
  K: "#000044", // /

  L: "#ffffff", // \
  M: "#ffaaaa", // |
  N: "#ffffaa", // |  Used for empty spaces
  O: "#aaffaa", // |
  P: "#aaffff", // |
  Q: "#aaaaff", // /

  X: "#D0A000", // Point
};

async function start() {
  user_id = document.getElementById("user-id").value;
  //console.log(user_id)
  proxy_switch = document.getElementById("proxy-switch").checked;
  console.log(proxy_switch)

  if (proxy_switch) {
    server_ip = proxy_addr
    port = proxy_port
    ws_port = proxy_ws_port
  }

  document.getElementById("container").remove();

  var display_div = document.createElement("div");
  display_div.id = "display";
  document.body.appendChild(display_div);

  var canvas = document.createElement("canvas");
  canvas.id = "canvas";

  display_div.appendChild(canvas);
  await get_size();
  set_size();
  update();
}

function set_size() {
  var canvas = document.getElementById("canvas");
  pixel_size = 100;
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

async function get_size() {
  try {
    const response = await sendMessageAndAwaitResponse(`get_size ${user_id}`);
    if (response.includes("size:")) {
      size = response.replace("size:", "");
    } else {
      console.log(response);
    }
  } catch (error) {
    console.error("Error occurred:", error);
  }
}

async function get_pixels() {
  try {
    const response = await sendMessageAndAwaitResponse(`get_pixels ${user_id}`);
    if (response.includes("data:")) {
      raw_pixels = response.replace("data:", "");
    } else {
      console.log(response);
    }
  } catch (error) {
    console.error("Error occurred:", error);
  }
}

function draw_on_display(raw_pixels) {
  var c = document.getElementById("canvas");
  var ctx = c.getContext("2d");

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      ctx.fillStyle = colors[raw_pixels[y * size + x]];
      ctx.fillRect(x * pixel_size, y * pixel_size, pixel_size, pixel_size);
      ctx.stroke();
    }
  }
}

async function update() {
  await get_size();
  await get_pixels();
  set_size();
  draw_on_display(raw_pixels);

  setTimeout(update, 1000);
}
