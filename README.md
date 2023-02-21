# What is this project?
The CustomizableSocketServer is designed to be a lightweight, intuitive balance between structure and flexibility that allows for the quick, easy implementation of a TCP socket server and clients, when something like a full blown REST API creates too much latency, and you need constant connection.

## What is included?
1. Server, which can host many connections side by side using selectors module. Supports command input from authenticated admin clients. In addition to a predefined set of commands, user of the server can add aditional commands during instantiation of the server class
2. Client, which provides a basic foundation for TCP operations and message handling. Designed to be easily extendible with inheritance
3. Optimized for IDE's that support type hinting
4. SSL built in (will improve this later)