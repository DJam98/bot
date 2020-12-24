"""cogs.Checkin"""

import discord
from discord.ext import tasks, commands

from offthedialbot import utils
from offthedialbot.commands.signup import Signup


class Tournament(commands.Cog, command_attrs={'hidden': True}):
    """Cog holding tournament-related misc commands."""
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    @tasks.loop(hours=1)
    async def loop(self):
        """Task loop that assigns roles."""
        docs = utils.firestore.db.collection(u'tournaments').document(u'2KnLtpnPNjz2AE0OxwX5').collection(u'signups').stream()
        ids = [doc.id for doc in docs]

        guild = self.bot.get_guild(374715620052172800)
        role = guild.get_role(415767083691802624)

        for id in ids:
            user = guild.get_member(int(id))
            await user.add_roles(role)

        for sign in role.members:
            if not sign.id in ids:
                await sign.remove_roles(role)

    @loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @utils.deco.otd_only
    @utils.deco.tourney()
    @utils.deco.profile_required(competing=True)
    async def checkin(self, ctx: commands.Context):
        """Check in for the tournament."""
        # Check if check-in is not enabled
        if utils.tourney.get()['checkin'] is False:
            raise commands.errors.DisabledCommand
        # Check if the attendee has already checked in
        if utils.roles.has(ctx.author, "Checked In"):
            await utils.Alert(ctx, utils.Alert.Style.DANGER,
                              title="Already Checked-in",
                              description="You have already checked-in!")
            raise utils.exc.CommandCancel

        # Get Checked In role, or create it.
        ui: utils.CommandUI = await utils.CommandUI(ctx,
            discord.Embed(title="Check-in Form", color=utils.colors.COMPETING)
        )
        await Signup.profile_updated(ui, utils.Profile(ctx.author.id))
        if not (role := utils.roles.get(ctx, "Checked In")):
            role = await ui.ctx.guild.create_role(name="Checked In")

        # Check the attendee in
        await ui.ctx.author.add_roles(role)  # Add roles
        utils.time.Timer.delete(destination=ctx.author.id, author=ctx.me.id)  # Remove warning

        await ui.end(True)

    @commands.command(aliases=["competing", "registered"])
    @utils.deco.tourney()
    async def signedup(self, ctx):
        """Get number of people currently signed up for the tournament."""
        num = utils.dbh.metaprofiles.count({"reg.reg": True})
        embed = discord.Embed(
            title="Currently Signed-up:",
            description=f"`{num}`",
            color=utils.colors.COMPETING
        )
        if num_checkedin := len(utils.roles.get(ctx, "Checked In").members):
            embed.add_field(name="Currently Checked-in:", value=f"`{num_checkedin}`")
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @utils.deco.tourney()
    async def when(self, ctx):
        """Check when the tournament starts / ends registration relative to your timezone."""

    @when.command(aliases=["starts"])
    @utils.deco.tourney()
    async def start(self, ctx):
        ui, timezone = await self.ask_timezone(ctx)
        status, resp = await utils.smashgg.post(utils.smashgg.startat, ctx=ctx)
        timestamp = utils.time.Zone.add_offset(resp["data"]["tournament"]["startAt"], timezone)

        await ui.end(utils.Alert.create_embed(utils.Alert.Style.INFO,
            title="Tournament starts at:",
            description=self.display_time(timestamp, timezone)))

    @when.command(aliases=["closes", "reg", "registration"])
    @utils.deco.tourney()
    async def close(self, ctx):
        ui, timezone = await self.ask_timezone(ctx)
        status, resp = await utils.smashgg.post(utils.smashgg.registrationclosesat, ctx=ctx)
        timestamp = utils.time.Zone.add_offset(resp["data"]["tournament"]["registrationClosesAt"], timezone)

        await ui.end(utils.Alert.create_embed(utils.Alert.Style.INFO,
            title="Tournament registration closes at:",
            description=self.display_time(timestamp, timezone)))

    async def ask_timezone(self, ctx):
        ui: utils.CommandUI = await utils.CommandUI(ctx, discord.Embed(
            title="What timezone are you in?",
            description="ex: `UTC`, `AEST`, `EDT`"
        ))
        reply = await ui.get_valid_message(
            lambda m: utils.time.Zone.tz_offsets.get(m.content.upper(), False) is not False,
            {"title": "Invalid Timezone", "description": "Please enter a valid timezone."})
        return ui, reply.content.upper()

    @staticmethod
    def display_time(timestamp, timezone):
        return utils.time.User.display(timestamp, "%A, %b %d at %I:%M%p ") + timezone
