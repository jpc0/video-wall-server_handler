## Network API

The network API will use ZeroMQ as a communication's protocol, it will expect
the following JSON encoded data:

```
{
    "version": "0.1.0",
    "command": "display_image",
    "location": "http://fileserve.example.com/${guid}.jpeg",
}
```
```
{
    "version": "0.1.0",
    "command": "display_image_loop",
    "loop_time": 5, # Loop time in seconds
    "locations": [
        "http://fileserve.example.com/${guid}.jpeg",
        "http://fileserve.example.com/${guid}.jpeg",
        "http://fileserve.example.com/${guid}.jpeg",
        "http://fileserve.example.com/${guid}.jpeg",],
}
```
```
{
    "version": "0.1.0",
    "command": "stop_image",
}
```

It will always return the following JSON encoded data:
```
{
    "version": "0.1.0",
    "command": "info",
    "message": "This is an example info message",
}
```