# Usage

The micropython cloud manager is managaed using the `mbm` command line utility on the main service host.

The `mbm` utility supports managing the cloud service as well as performing operations on boards running micropython
that are connecting to the cloud management server.


## Service Commands

Before any commands can be run the service needs to be available.

### service-start

This command will start the cloudmanager service as a daemon process running as the user that starts it.

### service-stop

This command stops the running cloudmanager service.

### service-status

This command shows the status of the cloudmanager service.

## Board Operation Commands

### board-scan

The board-scan command will scan for unconfigured micropython boards running the cloudclient.

**Note** - This command currently only works on Linux

### board-list

The board-list command shows all boards that are registered with the cloudmanager service.

### board-print

The board-print command will print text to the specified boards console

### board-rename

The board-rename command will change the name of a managed board

usage: mbm board-rename [-h] board name

positional arguments:
  board       Board to rename
  name        New board name

### board-execute

The board-execute command will send the command from the stdin stream to all the boards specified and return the output

usage: mbm board-execute [-h] [--debug] board

positional arguments:
  board       Board(s) to execute the code on

**Note** - The current micropython firmware on the wipy and wipy2 boards does not currently return output.

### board-upload

The board-upload command will upload a file to all of the specified boards.

usage: mbm board-upload [-h] board filename dest

positional arguments:
  board       Message to print on the console
  filename    File to upload
  dest        Destination filename (optional)

