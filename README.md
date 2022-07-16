# PyArmor-Unpacker
I decided it was time there was a proper PyArmor unpacker released. All the ones that currentently are public are either outdated, not working at all or only giving partial output. I plan on making this one support the latest version.

## How to use it
There are 3 different methods for unpacking PyArmor, in the methods folder in this repository you will find all the files needed for each method. Below you will find a detailed write-up on how I started all the way to the end product. I hope more people actually understand how it works this way rather than just using the tool. I recommend watching my YouTube series on [Python Reversing](https://www.youtube.com/playlist?list=PL7tLQ48v5ygquBfkhi4HRZSeMH0IT-Jw5) so you understand the basics.

### Method 1
TODO

### Method 2
TODO

### Method 3
TODO

## Write-Up
This is the long-awaited write-up about the full process I went through to deobfuscate or rather unpack PyArmor, I will go through all the research I did and at the end give 3 methods for unpacking PyArmor, they are all unique and applicable in different situations. I want to mention I didn’t know a lot about Python internals so it took a lot longer for me than for other people with more experience in Python internals.<br/>

PyArmor has a very extensive [documentation](https://pyarmor.readthedocs.io/en/latest/) on how they do everything, I would recommend you read that fully. PyArmor essentially loops through every code object and encrypts it. There is a fixed header and footer though. This depends on if the “wrap mode” is enabled, it is by default.<br/>
```
wrap header:

        LOAD_GLOBALS    N (__armor_enter__)     N = length of co_consts
        CALL_FUNCTION   0
        POP_TOP
        SETUP_FINALLY   X (jump to wrap footer) X = size of original byte code

changed original byte code:

        Increase oparg of each absolute jump instruction by the size of wrap header

        Obfuscate original byte code

        ...

wrap footer:

        LOAD_GLOBALS    N + 1 (__armor_exit__)
        CALL_FUNCTION   0
        POP_TOP
        END_FINALLY
```
<sup>From the [PyArmor docs](https://pyarmor.readthedocs.io/en/latest/how-to-do.html#how-to-obfuscate-python-scripts)</sup><br/>
In the header there is a call to the `__armor_enter__` function, which will decrypt the code object in memory. After the code object has finished the `__armor_exit__` function will be called which will re-encrypt the code object again so no decrypted code objects get left behind in memory.

When we compile a PyArmor script we can see there is the entry point file, and a pytransform folder. This folder contains a dll and an `__init__.py` file.<br/>
```
dist
│ test.py
└───pytransform
    | _pytransform.dll
    | __init__.py
```
The `__init__.py` file doesn’t have to do much with decrypting the code objects. It is mostly used so that we can import the module.
It does some checks like what os you're using, if you’d like to read it, it’s open source so you can just open it like a normal Python script.<br/>
The most important thing it does is loading the `_pytransform.dll` and exposing it’s functions to the Python interpreter’s globals. In all the scripts we can see that from pytransform it imports pyarmor_runtime.
```py
from pytransform import pyarmor_runtime
pyarmor_runtime()
__pyarmor__(__name__, __file__, b'\x50\x59\x41\x5...')
```
This function will create all the functions necessary to run PyArmor scripts, like the armor enter and exit function.

The first resource I found is [this](https://forum.tuts4you.com/topic/41945-python-pyarmor-my-protector/) thread on the forum of tuts4you, here the user `extremecoders` wrote a few posts on how he unpacked the PyArmor protected file. He edited the CPython source code to dump the marshal of every code object that gets executed.<br/>
While this method is great for exposing all the constants, it’s less ideal if you want to get the bytecode, this is because:
1. You will have to find the main module code object, since all code objects get dumped, even the ones from modules etc it will be more difficult to find the main one.
2. The code object won’t have been decrypted yet by PyArmor since that only happens when the armor enter function gets called, which is at the start of the code object. Since the armor enter function decrypts it in memory it won’t get dumped by CPython.

There are some people that have experimented with dumping the decrypted code objects from memory by injecting Python code.<br/>
In [this](https://www.youtube.com/watch?v=P9zhLuKOqT8) video someone demonstrates how he disassembles all the decrypted functions in memory.<br/>
However, he hasn’t found out yet how to dump the main module, only functions. Thankfully he published his code he used to inject Python code. On the [GitHub repository](https://github.com/call-042PE/PyInjector) we can see that he creates a dll in which he calls an exported function from the Python dll to execute simple Python code. Currently he only added support for finding the Python dlls for versions 3.7 to 3.9 but you can easily add more versions by modifying the source and recompiling it. He made it so it executes the code found in code.py, this way it’s easy to edit the Python code without having to rebuild the project every time.<br/>
In the repository he includes a Python file which will dump all the function’s names to a file with their corresponding address in memory, if there is no memory found it means it hasn’t been called yet so it also hasn’t been decrypted yet. 
```py
# Copyright holder: https://github.com/call-042PE
# License: GNU GPL v3.0 (https://github.com/call-042PE/PyInjector/blob/main/LICENSE)
import os,sys,inspect,re,dis,json,types

hexaPattern = re.compile(r'\b0x[0-9A-F]+\b')
def GetAllFunctions(): # get all function in a script
    functionFile = open("dumpedMembers.txt","w+")
    members = inspect.getmembers(sys.modules[__name__]) # the code will take all the members in the __main__ module, the main problem is that it can't dump main code function
    for member in members:
        match = re.search(hexaPattern,str(member[1]))
        if(match):
            functionFile.write("{\"functionName\":\""+str(member[0])+"\",\"functionAddr\":\""+match.group(0)+"\"}\n")
        else:
            functionFile.write("{\"functionName\":\""+str(member[0])+"\",\"functionAddr\":null}\n")
    functionFile.close()

GetAllFunctions()
```
<sup>From [call-042PE's repository](https://github.com/call-042PE/PyInjector/blob/main/src/GetAllFunctions.py)</sup><br/>
In the code you can see he added a comment saying the problem he has is that he can’t access the main module code object.<br/>
After a lot of Googling I was stumped to find nothing about how to get the current running code object. Sometime later in an unrelated project I saw a function call to `sys._getframe()`. I did some research on [what it does](https://docs.python.org/3/library/sys.html#sys._getframe), it gets the current running frame. You can give an integer as an argument which will walk up the callstack and get the frame at a specific index. Now the reason that this is important is because a frame in Python is basically just a code object but with more information about it’s state in memory. To get the code object from a frame we can use the .f_code attribute, you will also be familiar with this if you have created a custom CPython version which dumps the code objects that get executed as we also get the code object from a frame there. So now we have figured out how to get the current running code object, we can simply walk up the callstack until we find the main module, which will be decrypted. Now we’ve pretty much figured out the main idea of how to unpack PyArmor. I’ll now show 3 methods of unpacking that I have personally found useful in different situations. The first one requires to inject Python code, so you’ll have to run the PyArmor script. When we dump the main code object like I explained above the main problem will be that some functions will still be encrypted, thus the first methods invokes the PyArmor runtime function so that all the functions needed to decrypt the code objects are loaded, like __armor_enter__ and __armor_exit__. This seems like a pretty simple thing to do but PyArmor did think of this. They implemented a restrict mode. You can specify this when compiling a PyArmor script, by default the restrict mode is 1. I haven’t tested every restrict mode out but it works for the default one. When we try to 
