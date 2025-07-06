from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient


class VariationsDB:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.mongo_client = mongo_client
        self.variations_collection = self.mongo_client['ITI'].variations25  # todo

    async def save_variations(self, variations: dict[str, list[dict]]):
        """
        Save the check_variations to the database

        :param variations: The check_variations to save grouped by date. Example: {'date': [{'date': 'date', 'teacher': 'teacher', 'subject': 'subject'}]}
        :return:
        """
        for date, variations in variations.items():
            # Save date in Date format
            await self.variations_collection.update_one(
                {'date': datetime.strptime(date, '%d-%m-%Y')},
                {'$set': {'date': datetime.strptime(date, '%d-%m-%Y'), 'check_variations': variations}},
                upsert=True
            )

    async def get_variations_by_date(self, date: str) -> list:
        """
        Get the check_variations for a specific date

        :param date: The date to get the check_variations for (dd-mm-yyyy)
        :return: The check_variations for the given date
        """

        # Find the check_variations for the given date (saved in Date format)
        variations = await self.variations_collection.find_one(
            {'date': datetime.strptime(date, '%d-%m-%Y')},
            {'_id': 0, 'date': 0}
        )

        return variations['check_variations'] if variations is not None else []

    async def get_classes_scoreboard(self) -> list:
        """
        Get the scoreboard for the classes, ordered by the number of check_variations for each class

        :return: The scoreboard
        """

        # Filter only _id != '' and 2 <= _id.length < 10
        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$check_variations'},
            {'$group': {'_id': '$check_variations.class', 'check_variations': {'$sum': 1}}},
            {'$match': {'$and': [{'_id': {'$ne': ''}}, {'_id': {'$regex': r'^\w{2,10}$'}}]}},
            {'$sort': {'check_variations': -1}}
        ]).to_list()

        return scoreboard

    async def get_variations_per_class_age(self, class_age: int) -> list:
        """
        Get the check_variations for the given class age. Example: class_age = 4, returns the check_variations for all classes in the 4th grade (4A, 4B, 4C, 4D, 4E, 4F)

        :param class_age: The class age to get the check_variations for
        :return: The check_variations for the given class age
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$check_variations'},
            {'$match': {'check_variations.class': {'$regex': f'^{class_age}[A-Z]+'}}},
            {'$group': {'_id': '$check_variations.class', 'check_variations': {'$sum': 1}}},
            {'$sort': {'check_variations': -1}}
        ]).to_list()

        return scoreboard

    async def get_variations_summary(self) -> dict:
        """
        Get the check_variations grouped by class age. Example: 4A, 4B, 4C, 4D, 4E, 4F are all in the 4th grade, so they are grouped together.

        :return: The check_variations grouped by class age
        """

        scoreboard = await self.get_classes_scoreboard()

        summary = {}

        for item in scoreboard:
            class_age = item['_id'][0]
            if not class_age.isdigit():
                continue

            if class_age not in summary.keys():
                summary[class_age] = item['check_variations']
            else:
                summary[class_age] += item['check_variations']

        # Sort the summary by class age
        summary = {k: v for k, v in sorted(summary.items(), key=lambda i: i[0])}

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
        classes_count = {k: v for k, v in sorted(classes_count.items(), key=lambda i: i[0])}

        return classes_count

    async def get_professors_scoreboard(self) -> list:
        """
        Get the scoreboard for each professor

        :return: The scoreboard for each professor
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$check_variations'},
            {'$group': {'_id': '$check_variations.teacher', 'check_variations': {'$sum': 1}}},
            {'$sort': {'check_variations': -1}}
        ]).to_list()

        return scoreboard

    async def get_yearly_stats(self) -> dict:
        """
        Get the yearly stats (number of check_variations per month)

        :return: Dict containing the length of check_variations per month ordered by month
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$check_variations'},
            {'$group': {'_id': {'$month': '$date'}, 'check_variations': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]).to_list()

        # Convert scoreboard to dict
        scoreboard = {item['_id']: item['check_variations'] for item in scoreboard}

        # Add months with no check_variations
        for month in range(1, 13):
            if month not in scoreboard.keys():
                scoreboard[month] = 0

        # Sort scoreboard by month
        scoreboard = {k: v for k, v in sorted(scoreboard.items(), key=lambda item: item[0])}

        return scoreboard

    async def get_monthly_stats(self, month: int) -> dict:
        """
        Get the monthly stats (number of check_variations per day)

        :param month: The month to get the stats for
        :return: Dict containing the length of check_variations per day ordered by day
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$check_variations'},
            {'$match': {'date': {'$regex': f'^[0-9]+-{month}-[0-9]+$'}}},
            {'$group': {'_id': {'$dayOfMonth': '$date'}, 'check_variations': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]).to_list()

        # Convert scoreboard to dict
        scoreboard = {item['_id']: item['check_variations'] for item in scoreboard}

        # Add days with no check_variations
        for day in range(1, 32):
            if day not in scoreboard.keys():
                scoreboard[day] = 0

        # Sort scoreboard by day
        scoreboard = {k: v for k, v in sorted(scoreboard.items(), key=lambda item: item[0])}

        return scoreboard

    async def get_weekday_stats(self) -> dict:
        """
        Get the weekday stats (number of check_variations per weekday), each weekday divided by the number of documents in the DB for that weekday

        :return: Dict containing the length of check_variations per weekday ordered by weekday
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$check_variations'},
            {'$group': {'_id': {'$dayOfWeek': '$date'}, 'check_variations': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]).to_list()

        # Convert scoreboard to dict
        scoreboard = {item['_id']: item['check_variations'] for item in scoreboard}

        # Add weekdays with no check_variations
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
        Get the hourly stats (number of check_variations per hour got from each variation in hour field)

        :return: Dict containing the length of check_variations per hour ordered by hour (1-6 inclusive)
        """

        scoreboard = await self.variations_collection.aggregate([
            {'$unwind': '$check_variations'},
            {'$group': {'_id': '$check_variations.hour', 'check_variations': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]).to_list()

        # Convert the scoreboard to a dict
        scoreboard = {item['_id']: item['check_variations'] for item in scoreboard}

        # Fill the scoreboard with the missing hours
        for hour in range(1, 7):
            if str(hour) not in scoreboard.keys():
                scoreboard[str(hour)] = 0

        # Sort the scoreboard by hour
        scoreboard = {k: v for k, v in sorted(scoreboard.items(), key=lambda item: item[0])}

        return scoreboard
