# Method #1
# By svenskithesource (https://github.com/Svenskithesource)
# Made for (https://github.com/Svenskithesource/PyArmor-Unpacker)

import opcode, types, marshal

RETURN_OPCODE = opcode.opmap["RETURN_VALUE"].to_bytes(2, byteorder='little') # Convert to bytes so it can be added to bytes easier later on
SETUP_FINALLY = opcode.opmap["SETUP_FINALLY"]
EXTENDED_ARG = opcode.opmap["EXTENDED_ARG"]
LOAD_GLOBAL = opcode.opmap["LOAD_GLOBAL"]

# All absolute jumps
JUMP_ABSOLUTE = opcode.opmap.get("JUMP_ABSOLUTE")
CONTINUE_LOOP = opcode.opmap.get("CONTINUE_LOOP")
POP_JUMP_IF_FALSE = opcode.opmap.get("POP_JUMP_IF_FALSE")
POP_JUMP_IF_TRUE = opcode.opmap.get("POP_JUMP_IF_TRUE")
JUMP_IF_FALSE_OR_POP = opcode.opmap.get("JUMP_IF_FALSE_OR_POP")
JUMP_IF_TRUE_OR_POP = opcode.opmap.get("JUMP_IF_TRUE_OR_POP")

absolute_jumps = [JUMP_ABSOLUTE, CONTINUE_LOOP, POP_JUMP_IF_FALSE, POP_JUMP_IF_TRUE, JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP]

double_jump = True if sys.version_info.major == 3 and sys.version_info.minor >= 10 else False

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

    load_exit_function = b''.join(i.to_bytes(1, byteorder='big') for i in [LOAD_GLOBAL, obj.co_names.index("__armor_exit__")])
    fake_exit = obj.co_code.find(load_exit_function) - 2
    

    raw_code = bytearray(raw_code)
    i = 0
    while i < len(raw_code):
        op = raw_code[i]
        if op in absolute_jumps:
            argument = calculate_arg(raw_code, i)

            if double_jump: argument *= 2

            if argument == fake_exit:
                raw_code[i] = opcode.opmap["RETURN_VALUE"] # Got to use this because the variable is converted to bytes
                continue

            new_arg = argument - (try_start+2)

            extended_args, new_arg = calculate_extended_args(new_arg)

            for extended_arg in extended_args:
                raw_code.insert(i, EXTENDED_ARG)
                raw_code.insert(i+1, extended_arg if not double_jump else extended_arg//2)
                i += 2

            raw_code[i+1] = new_arg if not double_jump else new_arg//2

        i += 2

    raw_code = bytes(raw_code)

    return obj.replace(co_code=raw_code)


code = marshal.loads(open("dumped.marshal", "rb").read())

fixed_code = output_code(code)

open("dumped.marshal", 'wb').write(marshal.dumps(fixed_code))