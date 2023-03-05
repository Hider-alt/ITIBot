from motor.motor_asyncio import AsyncIOMotorClient


class Variations:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.mongo_client = mongo_client
        self.variations_collection = self.mongo_client['ITI'].variations

    async def save_variations(self, variations: dict[list[dict]]):
        """
        Save the variations to the database

        :param variations: The variations to save grouped by date. Example: {'date': [{'date': 'date', 'teacher': 'teacher', 'subject': 'subject'}]}
        :return:
        """
        for date, variations in variations.items():
            await self.variations_collection.update_one(
                {'date': date},
                {'$set': {'date': date, 'variations': variations}},
                upsert=True
            )

    async def get_variations_by_date(self, date: str) -> list:
        """
        Get the variations for a specific date

        :param date: The date to get the variations for (dd-mm-yyyy)
        :return:
        """

        variations = await self.variations_collection.find_one(
            {'date': date},
            {'_id': 0, 'date': 0}
        )

        return variations['variations'] if variations is not None else []

    async def get_classes_scoreboard(self) -> list:
        """
        Get the scoreboard for the classes, ordered by the number of variations for each class

        :return: The scoreboard
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$group': {'_id': '$variations.class', 'variations': {'$sum': 1}}},
            {'$sort': {'variations': -1}}
        ]).to_list(None)

        return scoreboard

    async def get_variations_per_class_age(self, class_age: int) -> list:
        """
        Get the variations for the given class age. Example: class_age = 4, returns the variations for all classes in the 4th grade (4A, 4B, 4C, 4D, 4E, 4F)

        :param class_age: The class age to get the variations for
        :return:
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$match': {'variations.class': {'$regex': f'^{class_age}'}}},
            {'$group': {'_id': '$variations.class', 'variations': {'$sum': 1}}},
            {'$sort': {'variations': -1}}
        ]).to_list(None)

        return scoreboard

    async def get_variations_summary(self) -> dict:
        """
        Get the variations grouped by class age. Example: 4A, 4B, 4C, 4D, 4E, 4F are all in the 4th grade, so they are grouped together.

        :return: The variations grouped by class age
        """

        scoreboard = await self.get_classes_scoreboard()

        summary = {}

        for item in scoreboard:
            class_age = item['_id'][0]
            if class_age not in summary.keys():
                summary[class_age] = item['variations']
            else:
                summary[class_age] += item['variations']

        # Sort the summary by class age
        summary = {k: v for k, v in sorted(summary.items(), key=lambda item: item[0])}

        return summary

    async def get_classes_count(self, scoreboard=None) -> dict:
        """
        Get the number of classes grouped by class age

        :return: The number of classes grouped by class age
        """

        scoreboard = await self.get_classes_scoreboard() if scoreboard is None else scoreboard

        classes_count = {}

        for item in scoreboard:
            class_age = item['_id'][0]
            if class_age not in classes_count.keys():
                classes_count[class_age] = 1
            else:
                classes_count[class_age] += 1

        # Sort the summary by class age
        classes_count = {k: v for k, v in sorted(classes_count.items(), key=lambda item: item[0])}

        return classes_count

    async def get_professors_scoreboard(self):
        """
        Get the scoreboard for each professor

        :return: The scoreboard for each professor
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$group': {'_id': '$variations.teacher', 'variations': {'$sum': 1}}},
            {'$sort': {'variations': -1}}
        ]).to_list(None)

        return scoreboard