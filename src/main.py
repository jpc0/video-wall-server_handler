import threading
import datetime
import zmq


def worker(worker_url: str, pub_url: str, context: zmq.Context = None):
    context = context or zmq.Context.instance()

    z_pub_socket = context.socket(zmq.PUB)
    z_pub_socket.bind(pub_url)
    socket = context.socket(zmq.PAIR)
    socket.connect(worker_url)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    loop_start_time = None
    loop_cycle_duration = None
    image_cycle_time = None
    image_paths: list = []
    loop_running = False
    loop_iteration = 0
    while True:
        socks = dict(poller.poll((60.0/128.0)*1000))

        if socket in socks:
            message = socket.recv_json()

            # If we need to shut down the handler
            if message["command"] == "shutdown":
                socket.close()
                z_pub_socket.close()
                break

            # Display a single image to the screen, this will also cancel the
            # looping images

            if message["command"] == "display_image":
                loop_running = False
                z_pub_socket.send_json(message)

            if message["command"] == "adjust_color":
                loop_running = False
                z_pub_socket.send_json(message)

            # Begin the looping images

            if message["command"] == "display_image_loop":
                loop_start_time = datetime.datetime.now()
                loop_cycle_duration = message["loop_time"]
                image_cycle_time = loop_start_time + \
                    datetime.timedelta(seconds=loop_cycle_duration)
                image_paths = message["locations"]
                loop_running = True
                data = {
                    "version": "0.1.0",
                    "command": "info",
                    "info": loop_running
                }
                socket.send_json(data)
                data = {
                    "version": "0.1.0",
                    "command": "display_image",
                    "location": image_paths[loop_iteration],
                }
                z_pub_socket.send_json(message)
                loop_iteration = 0

        if loop_running:
            if datetime.datetime.now() >= image_cycle_time:
                loop_iteration += 1
                if loop_iteration >= len(image_paths):
                    loop_iteration = 0
                data = {
                    "version": "0.1.0",
                    "command": "display_image",
                    "location": image_paths[loop_iteration],
                }
                z_pub_socket.send_json(data)
                loop_start_time = datetime.datetime.now()
                image_cycle_time = loop_start_time + \
                    datetime.timedelta(seconds=loop_cycle_duration)


def main():
    HOST = 'tcp://*'
    REP_PORT = '9091'
    PUB_PORT = '7000'
    z_context = zmq.Context.instance()
    z_rep_socket = z_context.socket(zmq.REP)
    z_proc_socket = z_context.socket(zmq.PAIR)

    z_rep_socket.bind(f'{HOST}:{REP_PORT}')
    z_proc_socket.bind('inproc://looped')

    poller = zmq.Poller()
    poller.register(z_rep_socket, zmq.POLLIN)

    thread = threading.Thread(target=worker, args=(
        "inproc://looped", f"{HOST}:{PUB_PORT}"))
    thread.daemon = True
    thread.start()

    while True:
        try:
            socks = dict(poller.poll((60.0/128.0)*1000))
        except KeyboardInterrupt:
            data = {
                "version": "0.1.0",
                "command": "shutdown",
            }
            z_proc_socket.send_json(data)
            break

        if z_rep_socket in socks:
            message = z_rep_socket.recv_json()
            if message["command"] == "display_image":
                z_proc_socket.send_json(message)
                data = {
                    "version": "0.1.0",
                    "command": "info",
                    "message": "Message sent",
                }
                z_rep_socket.send_json(data)

            if message["command"] == "adjust_color":
                z_proc_socket.send_json(message)
                data = {
                    "version": "0.1.0",
                    "command": "info",
                    "message": "Message sent",
                }
                z_rep_socket.send_json(data)

            if message["command"] == "display_image_loop":
                z_proc_socket.send_json(message)
                is_running = z_proc_socket.recv_json()
                if is_running["info"] == True:
                    data = {
                        "version": "0.1.0",
                        "command": "info",
                        "message": "Loop initiated",
                    }
                    z_rep_socket.send_json(data)
                else:
                    data = {
                        "version": "0.1.0",
                        "command": "info",
                        "message": "Failed to start loop",
                    }
                    z_rep_socket.send_json(data)

    z_rep_socket.close()
    z_proc_socket.close()
    z_context.term()


if __name__ == "__main__":
    main()
