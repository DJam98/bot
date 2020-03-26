"""$test mutate"""
from offthedialbot import utils


@utils.deco.require_role("Developer")
async def main(ctx):
    profiles = utils.dbh.profiles.find({})
    for profile in profiles:

        utils.dbh.profiles.replace_one({"_id": profile["_id"]}, {
            "_id": profile["_id"],
            "IGN": profiles["status"]["IGN"],
            "SW": profiles["status"]["SW"],
            "Ranks": profiles["status"]["Ranks"],
            "stylepoints": profiles["stylepoints"],
            "cxp": profiles["cxp"],
            "signal": profiles["signal_strength"],
        })

        utils.dbh.metaprofiles.insert_one({
            "_id": profiles["_id"],
            "banned": profile["meta"]["banned"],
            "smashgg": profile["meta"]["smashgg"],
            "reg": {
                "reg": profile["meta"]["competing"],
                "code": profile["meta"]["confirmation_code"],
            }
        })
    await utils.Alert(ctx, utils.Alert.Style.SUCCESS, title="Mutate complete.", description="Remove this command as soon as possible")
