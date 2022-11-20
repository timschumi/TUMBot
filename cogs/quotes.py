import re

import discord
from discord.ext import commands

import basedbot


class Quotes(commands.Cog):
    """Manages quotes"""

    def __init__(self, bot):
        self.bot = bot

        self._var_pretty = self.bot.conf.var("quotes.pretty")

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx, *, search=""):
        """Displays one random quote"""

        search = "%" + re.sub(r"[^\x00-\x7F]+", "_", search) + "%"

        with self.bot.db.get(ctx.guild.id) as db:
            quote = db.execute(
                "SELECT content FROM quotes WHERE LOWER(content) LIKE ? ORDER BY RANDOM() LIMIT 1",
                (search,),
            ).fetchall()

        if len(quote) == 0:
            await ctx.send("No quotes found!")
            return

        quote = quote[0][0]

        if (
            self._var_pretty.get(ctx.guild.id) == "0"
            or "\n" in quote
            or re.search(r"<([@#])[0-9]+>", quote)
        ):
            await ctx.send(quote)
            return

        # Try to split quote
        matches = list(re.finditer(r" [-~] ", quote))

        if len(matches) < 1:
            quoteparts = [quote]
        else:
            match = matches[-1]
            quoteparts = [
                quote[0 : match.start()].strip(),
                quote[match.end() :].strip(),
            ]

        embed = discord.Embed(description=f"*{quoteparts[0]}*", color=0x36393F)

        if len(quoteparts) > 1 and quoteparts[1].strip() != "":
            embed.add_field(name=f"- **{quoteparts[1]}**", value="\u200b")

        await ctx.send(embed=embed)

    @quote.command()
    @basedbot.has_permissions("quotes.add")
    async def add(self, ctx, *, content):
        """Adds a quote"""

        content = await commands.clean_content(fix_channel_mentions=True).convert(
            ctx, content
        )

        with self.bot.db.get(ctx.guild.id) as db:
            result = db.execute(
                "SELECT COUNT(*) FROM quotes WHERE content = ?", (content,)
            ).fetchall()

        if result[0][0] > 0:
            await ctx.send("This quote already exists.")
            return

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("INSERT INTO quotes (content) VALUES (?)", (content,))

        await ctx.message.add_reaction("\U00002705")

    @quote.command()
    @basedbot.has_permissions("quotes.list")
    async def list(self, ctx, *, search=""):
        """Lists all the quotes"""

        search = "%" + re.sub(r"[^\x00-\x7F]+", "_", search) + "%"

        with self.bot.db.get(ctx.guild.id) as db:
            quotes = db.execute(
                "SELECT content FROM quotes WHERE LOWER(content) LIKE ? ORDER BY content",
                (search,),
            ).fetchall()

        if len(quotes) == 0:
            await ctx.send("No quotes found.")
            return

        await self.bot.send_paginated(
            ctx, [quote[0] for quote in quotes], linefmt="{}\n\n"
        )

    @quote.command()
    @basedbot.has_permissions("quotes.delete")
    async def delete(self, ctx, *, search):
        """Removes a quote"""

        search = "%" + re.sub(r"[^\x00-\x7F]+", "_", search) + "%"

        with self.bot.db.get(ctx.guild.id) as db:
            resulting_ids = db.execute(
                "SELECT rowid FROM quotes WHERE LOWER(content) LIKE ? ORDER BY content",
                (search,),
            ).fetchall()

        if len(resulting_ids) > 1:
            await ctx.send(
                "Only one quote at a time can be removed, to prevent admin-abuse."
            )
            return
        if len(resulting_ids) == 0:
            await ctx.send(
                "No quotes could be found. What does not exist cant be deleted. \U0001F427"
            )
            return

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("DELETE FROM quotes WHERE rowid = (?)", (resulting_ids[0][0],))

        await ctx.message.add_reaction("\U00002705")


async def setup(bot):
    # pylint: disable=missing-function-docstring
    bot.conf.register(
        "quotes.pretty",
        default="0",
        conv=bool,
        description="Whether to make quotes prettier.",
    )
    bot.perm.register("quotes.add", base="administrator", pretty_name="Add quotes")
    bot.perm.register(
        "quotes.delete", base="administrator", pretty_name="Delete quotes"
    )
    bot.perm.register("quotes.list", base="administrator", pretty_name="List quotes")
    await bot.add_cog(Quotes(bot))
