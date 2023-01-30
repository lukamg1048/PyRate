from dotenv import dotenv_values

values = dotenv_values()
token = values.get("DISCORD_TOKEN")