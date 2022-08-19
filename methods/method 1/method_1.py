# Method #1
# By svenskithesource (https://github.com/Svenskithesource)
# Made for (https://github.com/Svenskithesource/PyArmor-Unpacker)

import opcode, types, marshal

RETURN_OPCODE = opcode.opmap["RETURN_VALUE"].to_bytes(2, byteorder='little') # Convert to bytes so it can be added to bytes easier later on
SETUP_FINALLY = opcode.opmap["SETUP_FINALLY"]
EXTENDED_ARG = opcode.opmap["EXTENDED_ARG"]

def find_first_opcode(co: bytes, op_code: int):
    for i in range(0, len(co), 2):
        if co[i] == op_code:
            return i
    raise ValueError("Could not find the opcode")


def get_arg_bytes(co: bytes, op_code_index: int) -> bytearray:
    """
    This function calculate the argument of a call while considering the EXTENDED_ARG opcodes that may come before that
    """
    result = bytearray()
    result.append(co[op_code_index+1])

    checked_opcode = op_code_index - 2
    while checked_opcode >= 0 and co[checked_opcode] == EXTENDED_ARG:
        result.insert(0, co[checked_opcode + 1])
        checked_opcode-=2
    return result

def calculate_arg(co: bytes, op_code_index: int) -> int:
    return int.from_bytes(get_arg_bytes(co, op_code_index), 'big')


def output_code(obj):
    if isinstance(obj, types.CodeType):
        # TODO I think there is a bug here because the prints are really weird.
        if "pytransform" in obj.co_freevars:
            #  obj.co_name not in ["<lambda>", 'check_obfuscated_script', 'check_mod_pytransform']:
            pass
        elif "__armor_enter__" in obj.co_names: 
            obj = handle_armor_enter(obj)
        else:
            pass

    return obj

def handle_armor_enter(obj: types.CodeType):
    raw_code = obj.co_code

    try_start = find_first_opcode(obj.co_code, SETUP_FINALLY)

    size = calculate_arg(obj.co_code, try_start)
    raw_code = raw_code[:try_start+size]

    raw_code = raw_code[try_start+2:]
    raw_code += RETURN_OPCODE # add return # TODO this adds return none to everything? what?
    return obj.replace(co_code=raw_code)


code = marshal.loads(open("dumped.marshal", "rb").read())

fixed_code = output_code(code)

open("dumped.marshal", 'wb').write(marshal.dumps(fixed_code))