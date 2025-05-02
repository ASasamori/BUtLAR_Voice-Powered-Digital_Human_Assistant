from call_vanna import interpret_vanna_msg


def help_world():
    response = interpret_vanna_msg("")
    print(f"{response}")

help_world()