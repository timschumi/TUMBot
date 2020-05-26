from discord.ext import commands
import re
import sqlite3


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def sql(self, ctx, *, query):
        """Executes a SQL-query"""

        matches = re.match(r'`(.*)`', query)
        if not matches:
            await ctx.send("Couldn't filter out the query that should be executed.")
            return

        query = matches.group(1)
        try:
            with self.bot.db.get(ctx.guild.id) as db:
                result = [dict(row) for row in db.execute(query).fetchall()]
        except sqlite3.OperationalError as e:
            await ctx.send(f"```{e}```")
            return

        if len(result) < 1:
            return

        keys = result[0].keys()
        key_length = {}

        for row in result:
            for key in keys:
                if not key in key_length:
                    key_length[key] = len(str(key))

                key_length[key] = max(key_length[key], len(str(row[key])))

        text = "|"

        for i in keys:
            text += f" {str(i).ljust(key_length[i])} |"

        text += "\n" + '-' * len(text)

        for row in result:
            newtext = "\n|"
            for key in keys:
                newtext += f" {str(row[key]).ljust(key_length[key])} |"

            # -6: Account for code block
            if len(text) + len(newtext) >= 2000 - 6:
                await ctx.send(f"```{text}```")
                text = ""

            text += newtext

        await ctx.send(f"```{text}```")

    @commands.command(aliases=['purge'])
    @commands.cooldown(2, 600, type=commands.BucketType.default)
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, amount=10):
        """Removes a given amount of messages"""

        if amount <= 0:
            await ctx.send('"Was bist du für ein Idiot" ~ Johannes Stöhr (Betrag <= 0 ist unmöglich!)')
            return
        if amount > 20:
            await ctx.send("Zu großer Betrag!")
            return
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"**{amount}** Nachrichten wurden von **{ctx.author}** gelöscht.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def flatten(self, ctx):
        """Flattens all the previous texts in this channel into a wall of text"""

        async with ctx.channel.typing():
            text = ""

            async for message in ctx.channel.history(limit=None, oldest_first=True):
                # Skip command
                if ctx.message.id == message.id:
                    continue

                # Skip own messages
                if self.bot.user.id == message.author.id:
                    continue

                if len(text) + len(message.clean_content) + 1 > 2000:
                    await ctx.send(text)
                    text = ""

                text += message.clean_content + " "

            if len(text) > 0:
                await ctx.send(text)


def setup(bot):
    bot.add_cog(Admin(bot))
