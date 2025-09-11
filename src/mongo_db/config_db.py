from motor.motor_asyncio import AsyncIOMotorClient


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

    async def get_current_school_year(self) -> int:
        """
        Get the current school year from the database

        :return: The current school year (e.g. 24 for the 2023/2024 school year)
        """

        current_school_year = await self.variations_collection.find_one(
            {'_id': 'current_school_year'},
            {'_id': 0, 'current_school_year': 1}
        )

        if not current_school_year:
            await self.variations_collection.insert_one(
                {'_id': 'current_school_year', 'current_school_year': 26}
            )
            return 26

        return current_school_year['current_school_year'] if current_school_year else 26

    async def upgrade_school_year(self) -> None:
        """
        Upgrade the current school year in the database (e.g. from 23 to 24)

        :return: None
        """

        current_school_year = await self.get_current_school_year()
        new_school_year = current_school_year + 1

        await self.variations_collection.update_one(
            {'_id': 'current_school_year'},
            {'$set': {'current_school_year': new_school_year}},
            upsert=True
        )
