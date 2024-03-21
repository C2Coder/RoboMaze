server_ip = '10.0.1.30';
http_port = 8000;
ws_port = 8001;
proxy_server_ip = 'hotncold.ddns.net';
proxy_http_port = 8080;
proxy_ws_port = 8001;
update_interval = 1000;
user_id = "c2c"; // default id

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
  console.log(proxy_switch);

  if (proxy_switch) {
    server_ip = proxy_server_ip;
    http_port = proxy_http_port;
    ws_port = proxy_ws_port;
  }

  document.getElementById("container").remove();

  var display_div = document.createElement("div");
  display_div.id = "display";
  document.body.appendChild(display_div);

  var canvas = document.createElement("canvas");
  canvas.id = "canvas";

  display_div.appendChild(canvas);

  connectAndUpdate();
}

async function connectAndUpdate() {
  return new Promise((resolve) => {
    const socket = new WebSocket("ws://" + server_ip + ":" + ws_port);

    let intervalId;

    socket.addEventListener("open", (event) => {
      console.log("WebSocket Connection opened:", event);

      socket.send("get_pixels " + user_id);

      intervalId = setInterval(() => {
        socket.send("get_pixels " + user_id);
      }, update_interval);
    });

    socket.addEventListener("message", (messageEvent) => {
      console.log("Received response:", messageEvent.data);
      raw_data = String(messageEvent.data);
      raw_array = raw_data.split(";");
      if (raw_array[0] == "error") {
        console.error(raw_data);
      } else if (raw_array.length == 3) {
        size = Number(raw_array[2]);
        pixels = raw_array[1];
        pixel_size = 100; // default value

        var canvas = document.getElementById("canvas");

        canvas.width = size * pixel_size;
        canvas.height = size * pixel_size;

        draw_to_display(pixels, size, pixel_size);
      }
    });

    socket.addEventListener("close", (closeEvent) => {
      console.log("WebSocket Connection closed:", closeEvent);
      clearInterval(intervalId);
      resolve();
    });

    socket.addEventListener("error", (errorEvent) => {
      console.error("WebSocket Connection error:", errorEvent);
      resolve();
    });
  });
}

function draw_to_display(_pixels, _size, _pixel_size) {
  console.log(_pixels);
  console.log(_size);
  console.log(_pixel_size);
  var c = document.getElementById("canvas");
  var ctx = c.getContext("2d");

  for (let y = 0; y < _size; y++) {
    for (let x = 0; x < _size; x++) {
      ctx.fillStyle = colors[_pixels[y * _size + x]];
      ctx.fillRect(x * _pixel_size, y * _pixel_size, _pixel_size, _pixel_size);
      ctx.stroke();
    }
  }
}
