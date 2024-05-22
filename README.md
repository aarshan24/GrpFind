

# SETUP
To setup finder all you have to do is:
                                                      
                                                      
-Variable at the top named LOG                                                      
  its value should have such a format {_WEBHOOKURL_}/messages/{_MESSAGEID_}                                                      
  message id is an id of some prevous message sent by a webhook                                                      
  this message has to be in the same channel as webhook  

-Variable at the top named GROUP                           
  replace its value with a webhook url where found gorups will be sent                                                                                             
  (group link format sent to discord channel https://roblox.com/groups/1313131313131)     

  
-make sure there is a file named cookies.txt in the same folder as finder script                            
  it should contain .ROBLOSECURITY cookies, in separate lines each                             
  each cookie allows to send 2k reqeusts per minute                            
  we can check 100 group ids per every request which gives 200k scanned groups per minute with every cookie                            
  for optimal performance I recommend using 10 cookies per every processor core (8 core processor = 80 cokies)                            
  you can adjust amount of used cookies by yourself but keep in mind that using too many cookies will result in big speed drops                            
  
-make sure there is a file named blocked_ids.txt in the same folder as finder script                            
  there will be saved ids of blocked groups                            
  group becomes blocked once it doesn't have owner but is locked or closed so you can't join and claim it                            
  because of that we won't check such a group ever again and waste time                            

-python                                              
  I recommend using python version 3.10                                                                   
  before starting script downlad required libraries using pip ( pip install _library_name_ )                                                                     
  here is a list of all libraries used by script:                                                                          
    multiprocessing                                                        
    time                                                        
    requests                            
    json                                                        
    threading                                                        
    multiprocessing                                                       
    aiohttp                                                        
    asyncio    
                       
  most of them are built in but if you get missing module error after launching script just run command provided above                                               
  run script with command python3.10 linux_finder.py                                                 
  (python_version file_name)
  








  

