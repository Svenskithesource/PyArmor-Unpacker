# Credit to extremecoders (https://forum.tuts4you.com/profile/79240-extreme-coders/) for writing the script
# Credit to me for adding the comments explaining it
import ctypes
from ctypes.wintypes import *

VirtualProtect = ctypes.windll.kernel32.VirtualProtect

VirtualProtect.argtypes = [LPVOID, ctypes.c_size_t, DWORD, PDWORD]
VirtualProtect.restype = BOOL

# Load the dll in memory, this is useful because once it's loaded in memory it won't need to get loaded again so all the changes we make will be kept, including the bootstrap bypass
h_pytransform = ctypes.cdll.LoadLibrary("pytransform\\_pytransform.dll")
pytransform_base = h_pytransform._handle # Get the memory address where the dll is loaded

print("[+] _pytransform.dll loaded at", hex(pytransform_base))

# We got this offset like I showed above with x64dbg, it's the first address where we start the NOP
patch_offset = 0x70A18F80 - pytransform_base
num_nops = 0x70A18FD5 - 0x70A18F80 # Minus the end address, this is the size that the NOP will be. The result will be 0x55

oldprotect = DWORD(0)
PAGE_EXECUTE_READWRITE = DWORD(0x40)

print("[+] Setting memory permissions")
VirtualProtect(pytransform_base+patch_offset, num_nops, PAGE_EXECUTE_READWRITE, ctypes.byref(oldprotect))

print("[+] Patching bootstrap restrict mode")
ctypes.memset(pytransform_base+patch_offset, 0x90, num_nops) # 0x90 is NOP

print("[+] Restoring memory permission")
VirtualProtect(pytransform_base+patch_offset, num_nops, oldprotect, ctypes.byref(oldprotect))


print("[+] All done! Pyarmor bootstrap restrict mode disabled")