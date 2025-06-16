from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

MONGO_URI = "mongodb://fitshield_ro:F!t%24h!3lD_Pr0D_ro@ec2-13-204-93-167.ap-south-1.compute.amazonaws.com:17018/?authMechanism=SCRAM-SHA-256&authSource=Fitshield"
#MONGO_URI = "mongodb://fitshield:fitshield123@13.235.70.79:27017/Fitshield?directConnection=true&appName=mongosh+2.4.2"
client = MongoClient(MONGO_URI)
db = client["Fitshield"]

def check_connection():
    try:
        client.admin.command('ping')
        return {
            "status": True,
            "message": "MongoDB connection successful."
        }
    except ConnectionFailure as e:
        return {
            "status": False,
            "message": f"MongoDB connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": False,
            "message": f"An unexpected error occurred: {str(e)}"
        }
