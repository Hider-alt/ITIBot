from datetime import datetime, date

from motor.motor_asyncio import AsyncIOMotorClient

from src.models.variation import Variation


class VariationsDB:
    def __init__(self, mongo_client: AsyncIOMotorClient, school_year: int = 26):
        self.__school_year = school_year
        self.mongo_client = mongo_client
        self.variations_collection = self.mongo_client['ITI'][f'variations{school_year}']

    async def create_collection(self):
        """
        Create the variations collection if it doesn't exist
        """

        existing_collections = await self.mongo_client['ITI'].list_collection_names()
        if f'variations{self.__school_year}' not in existing_collections:
            await self.mongo_client['ITI'].create_collection(self.variations_collection.name)

    @staticmethod
    def __classify_variations(variations: list[Variation]) -> tuple[list[Variation], list[Variation], list[Variation]]:
        """
        Classify the variations into new, edited and deleted, using "type" field

        :param variations: The variations to classify
        :return: A tuple containing the new variations and the deleted variations
        """

        add = [var for var in variations if var.type == 'new']
        edit = [var for var in variations if var.type == 'edited']
        delete = [var for var in variations if var.type == 'removed']

        return add, edit, delete

    @staticmethod
    def __group_variations_by_date(variations: list[Variation]) -> dict[date, list[Variation]]:
        """
        Group the variations by date

        :param variations: The variations to group
        :return: A dict containing the variations grouped by date
        """

        grouped = {}

        for var in variations:
            date = var.date.date()
            if date not in grouped:
                grouped[date] = [var]
            else:
                grouped[date].append(var)

        return grouped

    async def save_variations(self, variations: list[Variation]):
        """
        Save the variations to the database

        :param variations: The variations to save/delete
        """

        add, edit, delete = self.__classify_variations(variations)

        add_grouped = self.__group_variations_by_date(add)
        edit_grouped = self.__group_variations_by_date(edit)
        delete_grouped = self.__group_variations_by_date(delete)

        await self.add_variations(add_grouped)
        await self.edit_variations(edit_grouped)
        await self.delete_variations(delete_grouped)

    async def add_variations(self, variations: dict[date, list[Variation]]):
        """
        Add the variations to the database

        :param variations: The variations to add, grouped by date
        """

        for date, daily_vars in variations.items():
            await self.variations_collection.update_one(
                {'date': datetime(date.year, date.month, date.day)},
                {'$push': {'variations': {'$each': [var.to_dict() for var in daily_vars]}}},
                upsert=True
            )

    async def edit_variations(self, variations: dict[date, list[Variation]]):
        """
        Edit the variations in the database

        :param variations: The variations to edit, grouped by date
        """

        for date, vars in variations.items():
            for var in vars:
                await self.variations_collection.update_one(
                    {'date': datetime(date.year, date.month, date.day), 'variations.hour': var.hour, 'variations.class': var.class_name, 'variations.teacher': var.teacher},
                    {'$set': {
                        'variations.$.classroom': var.classroom,
                        'variations.$.substitute_1': var.substitute_1,
                        'variations.$.substitute_2': var.substitute_2,
                        'variations.$.notes': var.notes
                    }}
                )

    async def delete_variations(self, variations: dict[date, list[Variation]]):
        """
        Delete the variations from the database

        :param variations: The variations to delete, grouped by date
        """

        for date, vars in variations.items():
            await self.variations_collection.update_one(
                {'date': datetime(date.year, date.month, date.day)},
                {'$pull': {
                    'variations': {
                        '$or': [
                            {'hour': var.hour, 'class': var.class_name, 'teacher': var.teacher} for var in vars
                        ]
                    }
                }}
            )

    async def get_variations_by_date(self, *date: date) -> list[Variation] | None:
        """
        Get the variations for the given date(s)

        :param date: The date(s) to get the variations for
        :return: The variations for the given date(s)
        """
        if not date:
            raise ValueError("At least one date must be provided")

        variations = self.variations_collection.find(
            {'date': {'$in': [datetime(d.year, d.month, d.day) for d in date]}},
            {'_id': 0, 'variations': 1, 'date': 1}
        )

        if not variations:
            return []

        result = []
        async for doc in variations:
            result.extend([Variation.from_dict(var, doc['date']) for var in doc['variations']])

        return result

    async def get_classes_leaderboard(self) -> list:
        """
        Get the scoreboard for the classes, ordered by the number of variations for each class

        :return: The scoreboard
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$group': {'_id': '$variations.class', 'count': {'$sum': 1}}},
            {'$match': {'_id': {'$regex': r"^[0-9][A-Z]+$"}}},
            {'$sort': {'count': -1}}
        ]).to_list()

        return scoreboard

    async def get_variations_per_class_age(self, class_age: int) -> list:
        """
        Get the variations for the given class age. Example: class_age = 4, returns the variations for all classes in the 4th grade (4A, 4B, 4C, 4D, 4E, 4F)

        :param class_age: The class age to get the variations for
        :return: The variations for the given class age
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$match': {'variations.class': {'$regex': f'^{class_age}[A-Z]+'}}},
            {'$group': {'_id': '$variations.class', 'variations': {'$sum': 1}}},
            {'$sort': {'variations': -1}}
        ]).to_list()

        return scoreboard

    async def get_variations_summary(self) -> dict:
        """
        Get the variations grouped by class age. Example: 4A, 4B, 4C, 4D, 4E, 4F are all in the 4th grade, so they are grouped together.

        :return: The variations grouped by class age
        """

        scoreboard = await self.get_classes_leaderboard()

        summary = {}

        for item in scoreboard:
            class_age = item['_id'][0]
            if not class_age.isdigit():
                continue

            if class_age not in summary.keys():
                summary[class_age] = item['count']
            else:
                summary[class_age] += item['count']

        # Sort the summary by class age
        summary = {k: v for k, v in sorted(summary.items(), key=lambda i: i[0])}

        return summary

    async def get_classes_count(self, scoreboard=None) -> dict:
        """
        Get the number of classes grouped by class age

        :return: The number of classes grouped by class age
        """

        scoreboard = await self.get_classes_leaderboard() if scoreboard is None else scoreboard

        classes_count = {}

        for item in scoreboard:
            class_age = item['_id'][0]
            if class_age not in classes_count.keys():
                classes_count[class_age] = 1
            else:
                classes_count[class_age] += 1

        # Sort the summary by class age
        classes_count = {k: v for k, v in sorted(classes_count.items(), key=lambda i: i[0])}

        return classes_count

    async def get_professors_leaderboard(self) -> list:
        """
        Get the scoreboard for each professor

        :return: The scoreboard for each professor
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$group': {'_id': '$variations.teacher', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]).to_list()

        return scoreboard

    async def get_yearly_stats(self) -> dict:
        """
        Get the yearly stats (number of variations per month)

        :return: Dict containing the length of variations per month ordered by month
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$group': {'_id': {'$month': '$date'}, 'variations': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]).to_list()

        # Convert scoreboard to dict
        scoreboard = {item['_id']: item['variations'] for item in scoreboard}

        # Add months with no variations
        for month in range(1, 13):
            if month not in scoreboard.keys():
                scoreboard[month] = 0

        # Sort scoreboard by month
        scoreboard = {k: v for k, v in sorted(scoreboard.items(), key=lambda item: item[0])}

        return scoreboard

    async def get_monthly_stats(self, month: int) -> dict:
        """
        Get the monthly stats (number of variations per day)

        :param month: The month to get the stats for
        :return: Dict containing the length of variations per day ordered by day
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$match': {'date': {'$regex': f'^[0-9]+-{month}-[0-9]+$'}}},
            {'$group': {'_id': {'$dayOfMonth': '$date'}, 'variations': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]).to_list()

        # Convert scoreboard to dict
        scoreboard = {item['_id']: item['variations'] for item in scoreboard}

        # Add days with no variations
        for day in range(1, 32):
            if day not in scoreboard.keys():
                scoreboard[day] = 0

        # Sort scoreboard by day
        scoreboard = {k: v for k, v in sorted(scoreboard.items(), key=lambda item: item[0])}

        return scoreboard

    async def get_weekday_stats(self) -> dict:
        """
        Get the weekday stats (number of variations per weekday), each weekday divided by the number of documents in the DB for that weekday

        :return: Dict containing the length of variations per weekday ordered by weekday
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$group': {'_id': {'$dayOfWeek': '$date'}, 'variations': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]).to_list()

        # Convert scoreboard to dict
        scoreboard = {item['_id']: item['variations'] for item in scoreboard}

        # Add weekdays with no variations
        for weekday in range(1, 8):
            if weekday not in scoreboard.keys():
                scoreboard[weekday] = 0

        # Sort scoreboard by weekday
        scoreboard = {k: v for k, v in sorted(scoreboard.items(), key=lambda item: item[0])}

        # Get the number of documents for each weekday
        documents_count = await self.variations_collection.aggregate([
            {'$group': {'_id': {'$dayOfWeek': '$date'}, 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]).to_list()

        # Convert documents_count to dict
        documents_count = {item['_id']: item['count'] for item in documents_count}

        # Add weekdays with no documents
        for weekday in range(1, 8):
            if weekday not in documents_count.keys():
                documents_count[weekday] = 0

        # Sort documents_count by weekday
        documents_count = {k: v for k, v in sorted(documents_count.items(), key=lambda item: item[0])}

        # Divide the scoreboard by the number of documents for each weekday
        for weekday in scoreboard.keys():
            if documents_count[weekday] != 0:
                scoreboard[weekday] = scoreboard[weekday] / documents_count[weekday]

        return scoreboard

    async def get_hourly_stats(self) -> dict:
        """
        Get the hourly stats (number of variations per hour got from each variation in hour field)

        :return: Dict containing the length of variations per hour ordered by hour (1-6 inclusive)
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$variations'},
            {'$group': {'_id': '$variations.hour', 'variations': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]).to_list()

        # Convert the scoreboard to a dict
        scoreboard = {item['_id']: item['variations'] for item in scoreboard}

        # Fill the scoreboard with the missing hours (1-6 inclusive)
        for hour in range(1, 7):
            if hour not in scoreboard.keys():
                scoreboard[hour] = 0

        # Sort the scoreboard by hour
        scoreboard = {k: v for k, v in sorted(scoreboard.items(), key=lambda item: item[0])}

        return scoreboard
