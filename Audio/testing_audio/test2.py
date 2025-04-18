from test import interpret_vanna_msg


def help_world():
    response = interpret_vanna_msg("Who teaches computer organization?")
    print(f"{response}")

help_world()