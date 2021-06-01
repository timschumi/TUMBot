from discord.ext import commands


def _is_cs_server(guild_id):
    return guild_id in [628452781199589377, 752114765148455012]


async def _check_cs_server(ctx):
    if ctx.guild is None:
        return False

    return _is_cs_server(ctx.guild.id)


class Johannes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(_check_cs_server)
    async def johannes(self, ctx):
        """Sends a cute animal"""
        await ctx.send("\U0001F427")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if not _is_cs_server(message.guild.id):
            return

        lower = message.clean_content.lower()

        # Reactions
        if "johannes" in lower or "stöhr" in lower:
            await message.add_reaction('\U0001F427')
        if "lmu" in lower:
            await message.add_reaction(":lmuo:668091545878003712")


def setup(bot):
    bot.add_cog(Johannes(bot))
