from __future__ import annotations
import os

from dotenv import dotenv_values
from typing import Union

from disnake import ApplicationCommandInteraction, ModalInteraction
from db import DB

values = dotenv_values()
token = values.get("DISCORD_TOKEN")

Interaction = Union[ApplicationCommandInteraction, ModalInteraction]

main_dir = os.path.split(os.path.abspath(__file__))[0]
outputs_dir = os.path.join(main_dir, "outputs")

from models.snowflakes import Thread, User

async def fetch_thread(inter: Interaction) -> Thread:
    # Need to check if the the command is being called from an established thread...
    return await DB.get_thread_by_id(thread_id=inter.channel_id)

async def validate_request(inter: Interaction, thread: Thread):
    # ...that the caller is a part of that thread...
    author = User(inter.author.id)
    if author not in thread:
        raise ValueError("You are not a member of the current thread.")
    # ...and that they're actually at bat.
    if author != thread.next_user:
        raise ValueError("It is not your turn to make or rate a recommendation.")

async def validate_request_recommender(inter: Interaction, thread: Thread):
    #variation of above function that validates the user with an open recommendation 
    author = User(inter.author.id)
    if author not in thread:
        raise ValueError("You are not a member of the current thread.")
    if author == thread.next_user:
        raise ValueError("You're not the active recommender")

def build_table(title, headers : list[str], data : list[list], min_total_size = 30, max_column_size = 50):
    if len(headers) != len(data[0]):
        raise ValueError("Headers and data do not match")
    if min_total_size < len(title):
        min_total_size = len(title) + 2
    #calculate column sizes
    column_sizes = []
    for header in headers:
        column_sizes.append(len(header))
    for row in data:
        #print("row: %s" % row)
        for i in range(len(row)):
            if len( str(row[i])) > column_sizes[i]:
                column_sizes[i] = len(str(row[i]))
    for i in range(len(column_sizes)):
        if column_sizes[i] > max_column_size:
            column_sizes[i] = max_column_size
    #print(column_sizes)

    total_size = int(sum(column_sizes) + len(column_sizes) - 1)
    while total_size < min_total_size:
        for i in range(len(column_sizes)):
            column_sizes[i]+=1
        total_size = int(sum(column_sizes) + len(column_sizes) - 1)

    ret = "```\n"
    ret += '-'* (total_size+2) + '\n'
    right_pad = int(total_size - len(title))//2
    left_pad = int(total_size - len(title) - right_pad)
    #print("Total size: %d Right pad: %d Left pad: %d" % (total_size, right_pad, left_pad))
    ret += '|'+' '*left_pad + title + ' '*right_pad + '|\n\n'
    #ret += '|'+' '*total_size+"|\n"
    for i in range(len(headers)):
        header = headers[i]
        column_size = column_sizes[i]

        if len(header) > column_size:
            header = header[:column_size - 3] + "..."

        right_pad = int(column_size - len(header))//2
        left_pad = int(column_size - len(header) - right_pad)
        ret += '|' + ' '*left_pad + header + ' '*right_pad
    ret += "|\n\n"
    for row in data:
        for i in range(len(row)):
            datum = str(row[i])
            column_size = column_sizes[i]

            if len(datum) > column_size:
                datum = datum[:column_size - 3] + "..."

            right_pad = int(column_size - len(datum))//2
            left_pad = int(column_size - len(datum) - right_pad)
            ret += '|' + ' '*left_pad + datum + ' '*right_pad
        ret += "|\n\n"
    ret += '-'* (total_size+2) + '\n'
    ret += "```"

    return(ret)
    
if __name__ == "__main__":
    head = "col1", "test col2", "Column with length!"
    data = [
        ["data1", 5, "data3"],
        ["This is some data here", 321, "more daata"],
        ["Even more data", 4563.94, "surprise: more data"]
    ]
    build_table("Test table", head, data, 20)
