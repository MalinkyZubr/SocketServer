# base-server:
* supports basic connection functionality
* algorithm:
  * have 2 selectors for receiving incoming connections, and handling requests
  * must support both encrypted and unencrypted connections
  * must support password to access server
  * must support json and files
  * base server should automatically undertake basic operations
  * should be able to be used in inheritance in order to add specialized functionality