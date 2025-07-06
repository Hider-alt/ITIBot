from motor.motor_asyncio import AsyncIOMotorClient


# TODO: aggiungi che ciascun utente può scegliere se ricevere notifiche 1 volta al giorno oppure push


class ConfigDB:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.mongo_client = mongo_client
        self.variations_collection = self.mongo_client['ITI'].config

    async def get_classes(self) -> list[list[str]]:
        """
        Get the classes from the database grouped by year (5 lists, one for each year)

        :return: The classes (e.g. [['1A', '1B'], ['2A', '2B'], ...])
        """
        classes = await self.variations_collection.find_one(
            {'_id': 'classes'},
            {'_id': 0, 'classes': 1}
        )

        return classes['classes'] if classes else []

    async def set_classes(self, classes: list[list[str]]) -> None:
        """
        Set the classes in the database

        :param classes: The classes to set (e.g. [['1A', '1B'], ['2A', '2B'], ...])
        :return: None
        """

        await self.variations_collection.update_one(
            {'_id': 'classes'},
            {'$set': {'classes': classes}},
            upsert=True
        )
