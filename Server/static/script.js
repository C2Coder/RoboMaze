server_ip = '127.0.0.1';
http_port = 8888;
ws_port = 8001;
proxy_server_ip = 'hotncold.ddns.net';
proxy_http_port = 8080;
proxy_ws_port = 8001;
update_interval = 1000;
user_id = "c2c"; // default id

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

function drawArrow(ctx, fromx, fromy, tox, toy, arrowWidth, color) {
  //variables to be used when creating the arrow
  var headlen = 10;
  var angle = Math.atan2(toy - fromy, tox - fromx);

  ctx.save();
  ctx.fillStyle = color;
  ctx.strokeStyle = color;

  //starting path of the arrow from the start square to the end square
  //and drawing the stroke
  ctx.beginPath();
  ctx.moveTo(fromx, fromy);
  ctx.lineTo(tox, toy);
  ctx.lineWidth = arrowWidth;
  ctx.stroke();

  //starting a new path from the head of the arrow to one of the sides of
  //the point
  ctx.beginPath();
  ctx.moveTo(tox, toy);
  ctx.lineTo(
    tox - headlen * Math.cos(angle - Math.PI / 7),
    toy - headlen * Math.sin(angle - Math.PI / 7)
  );

  //path from the side point of the arrow, to the other side point
  ctx.lineTo(
    tox - headlen * Math.cos(angle + Math.PI / 7),
    toy - headlen * Math.sin(angle + Math.PI / 7)
  );

  //path from the side point back to the tip of the arrow, and then
  //again to the opposite side point
  ctx.lineTo(tox, toy);
  ctx.lineTo(
    tox - headlen * Math.cos(angle - Math.PI / 7),
    toy - headlen * Math.sin(angle - Math.PI / 7)
  );

  //draws the paths created above
  ctx.fill();
  ctx.stroke();
  ctx.restore();
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
      //console.log("Received response:", messageEvent.data);
      raw_data = String(messageEvent.data);
      raw_array = raw_data.split("\n");

      if (raw_array[0] == "error") {
        console.error(raw_data);
      } else if (raw_array[0] == "pong") {
        // nothing here
      } else if (raw_array.length > 5) {
        console.log(raw_array)
        maze_id = raw_array[0]
        raw_array.shift();
        
        world = raw_array[0]
        raw_array.shift();

        size = Number(raw_array[0]);
        raw_array.shift();


        pixels = "";
        for (let i = 0; i < size; i++) {
          pixels = pixels + raw_array[0];
          raw_array.shift();
        }
        empty_color = raw_array[0];
        raw_array.shift();
        wall_color = raw_array[0];
        raw_array.shift();

        collected_points = raw_array[0]; // not used
        raw_array.shift();

        pixel_size = 100; // default value

        var canvas = document.getElementById("canvas");

        canvas.width = size * pixel_size;
        canvas.height = size * pixel_size;

        var ctx = canvas.getContext("2d");

        _colors = [empty_color, wall_color];
        for (let y = 0; y < size; y++) {
          for (let x = 0; x < size; x++) {
            ctx.fillStyle = _colors[pixels[y * size + x]];
            ctx.fillRect(
              x * pixel_size,
              y * pixel_size,
              pixel_size,
              pixel_size
            );
            ctx.stroke();
          }
        }

        for (let i = 0; i < raw_array.length; i++) {
          data = raw_array[i].split(";");

          switch (data[0]) {
            case "usr":
              data.shift();
              // user_id, nick, x, y, rot, color, team, collected_points
              ctx.fillStyle = data[5];
              ctx.fillRect(
                data[2] * pixel_size,
                data[3] * pixel_size,
                pixel_size,
                pixel_size
              );
              ctx.stroke();

              gap = 0.3;
              arrow_color = "#000";

              switch (Number(data[4])) {
                case 0:
                  drawArrow(
                    ctx,
                    data[2] * pixel_size + 0.5 * pixel_size,
                    data[3] * pixel_size + pixel_size - gap * pixel_size,
                    data[2] * pixel_size + 0.5 * pixel_size,
                    data[3] * pixel_size + gap * pixel_size,
                    5,
                    arrow_color
                  );
                  break;

                case 1:
                  drawArrow(
                    ctx,
                    data[2] * pixel_size + gap * pixel_size,
                    data[3] * pixel_size + 0.5 * pixel_size,
                    data[2] * pixel_size + pixel_size - gap * pixel_size,
                    data[3] * pixel_size + 0.5 * pixel_size,
                    5,
                    arrow_color
                  );
                  break;

                case 2:
                  drawArrow(
                    ctx,
                    data[2] * pixel_size + 0.5 * pixel_size,
                    data[3] * pixel_size + gap * pixel_size,
                    data[2] * pixel_size + 0.5 * pixel_size,
                    data[3] * pixel_size + pixel_size - gap * pixel_size,
                    5,
                    arrow_color
                  );
                  break;

                case 3:
                  drawArrow(
                    ctx,
                    data[2] * pixel_size + pixel_size - gap * pixel_size,
                    data[3] * pixel_size + 0.5 * pixel_size,
                    data[2] * pixel_size + gap * pixel_size,
                    data[3] * pixel_size + 0.5 * pixel_size,
                    5,
                    arrow_color
                  );
                  break;

                default:
                  break;
              }

              break;

            case "point":
              data.shift();
              // x, y, color
              ctx.fillStyle = data[2];
              ctx.fillRect(
                data[0] * pixel_size,
                data[1] * pixel_size,
                pixel_size,
                pixel_size
              );
              ctx.stroke();
              break;

            case "key":
              data.shift();
              // [color, x, y, world_to_tp, x_to_tp, y_to_tp]
              ctx.fillStyle = data[0];
              ctx.fillRect(
                data[1] * pixel_size,
                data[2] * pixel_size,
                pixel_size,
                pixel_size
              );
              ctx.stroke();

              break;

            default:
              break;
          }
        }
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

function draw_to_display(
  _pixels,
  _size,
  _pixel_size,
  _empty_color,
  _wall_color
) {}
