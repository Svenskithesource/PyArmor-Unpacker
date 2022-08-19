import restrict_bypass, marshal

from pytransform import pyarmor_runtime
pyarmor_runtime()

exec(marshal.loads(open("dumped.marshal", "rb").read()))