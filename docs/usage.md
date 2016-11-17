# Command Line Interface

The micropython cloud manager command line interface is managaed using the 
`mbm` command line utility on the main service host.

The `mbm` utility supports managing the cloud service as well as performing 
operations on boards running micropython that are connecting to the cloud 
management server.

## Cloudmanager Service Management Comands

Before any commands can be run the service needs to be available.

### service-start

This command will start the cloudmanager service as a daemon process running 
as the user that starts it.

    $ mbm server-start
    Cloudmanager service is listening on: 192.168.1.127:18266
    $ 
    

### service-stop

This command stops the running cloudmanager service.

    $ mbm server-stop
    Service is shutdown
    $ 

### service-status

This command shows the status of the cloudmanager service.

    $ mbm server-status
    Running
    $ 

## Cloudmanager Board (client) commands

The Cloudmanager board commands are used to interact with boards running the
cloudmanager client.

All commands that talk to boards support hostlists range operators when specifying
the boards to operate on.  This makes it simple to perform the same operation on
multiple boards.

For example:

    esp8266-0[08-11],wipy2-[1,3,7]
    
Will operate on this list of boards:
    esp8266-008
    esp8266-009
    esp8266-010
    esp8266-011
    wipy2-1
    wipy2-3
    wipy2-7


### board-scan

The board-scan command will scan for unconfigured micropython boards running the 
cloudclient.

**Note** - This command currently only works on Linux

### board-list

The board-list command shows all boards that are registered with the cloudmanager 
service.

    $ mbm board-list
    Name       Platform                                           State     
    esp8266-1  esp8266                                            idle      
    esp8266-2  esp8266                                            idle      
    esp8266-3  esp8266                                            idle      
    wipy2-1    WiPy                                               idle      
    $ 

### board-rename

The board-rename command will change the name of a managed board

usage: mbm board-rename [-h] board new_name

positional arguments:
  board       Board to rename
  new_name    New board name
  
  $ mbm board-rename esp8266-5 esp8266-2
  $ 

### board-execute

The board-execute command will send the command from the stdin stream to all the boards specified and return 
the output

usage: mbm board-execute [-h] board

positional arguments:
  board       Range of board(s) to execute the code on

    $ mbm board-execute --debug esp8266-[1-3]
    print('hello')
    ## Executing on 'esp8266-1' ####################################################
    hello
    
    ## Executing on 'esp8266-2' ####################################################
    hello
    
    ## Executing on 'esp8266-3' ####################################################
    hello
    
    $ 

### board-upload

The board-upload command will upload a file to all of the specified boards.

usage: mbm board-upload [-h] board filename dest

positional arguments:
  board       Range of board(s) to upload to
  filename    File to upload
  dest        Destination filename (optional)
  
    $ mbm board-upload esp8266-[1-3] example_file example_file
    Copying file to esp8266-1:example_file
    Copying file to esp8266-2:example_file
    Copying file to esp8266-3:example_file
    $ mbm board esp8266-[1-3] ls
    ## 'ls' on 'esp8266-1' #########################################################
    boot.py
    etc
    main.py
    example_file
    ## 'ls' on 'esp8266-3' #########################################################
    boot.py
    etc
    main.py
    example_file
    ## 'ls' on 'esp8266-2' #########################################################
    boot.py
    etc
    main.py
    example_file
    $ 

### board-install

The board-install package will intall a package on the board(s) specified. 

Note: This command performs the download and unpack of the package files on the
      cloudmanager server so does not require upip or it's dependencies be installed
      on the boards being operated on.
      
    $ mbm board-install esp8266-[1-3] micropython-logging
    Installing package 'micropython-logging'
    Copying file to esp8266-1:lib/logging.py
    Copying file to esp8266-3:lib/logging.py
    Copying file to esp8266-2:lib/logging.py
    $ mbm board-execute esp8266-[1-3]
    import logging
    logging.info('Example log message')
    ## Executing on 'esp8266-1' ####################################################
    INFO:None:Example log message
    
    ## Executing on 'esp8266-3' ####################################################
    INFO:None:Example log message
    
    ## Executing on 'esp8266-2' ####################################################
    INFO:None:Example log message
    
    $ 

