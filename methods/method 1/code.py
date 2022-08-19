import sys, marshal

for frame in sys._current_frames().values(): # Loop all the threads running in the process
    if "frozen" in frame.f_code.co_filename: # Find the correct thread (when injecting this code it also creates a new thread so we need to find the main one)
        while frame.f_back.f_back != None: # NOTE the frame before None is the obfuscated one
            frame = frame.f_back # Keep going one frame back until we find the main frame (see NOTE above on how we identify it)
        code = frame.f_code
        break

open("dumped.marshal", "wb").write(marshal.dumps(code))