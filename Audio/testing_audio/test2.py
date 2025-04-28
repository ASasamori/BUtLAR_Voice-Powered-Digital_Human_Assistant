from test import interpret_vanna_msg


def help_world():
    response = interpret_vanna_msg("Where is Noa Margolin's location?")
    print(f"{response}")

help_world()