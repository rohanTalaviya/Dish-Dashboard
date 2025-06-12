from django.http import JsonResponse
from pymongo import MongoClient
from django.shortcuts import render

# MongoDB connection
MONGO_URI = "mongodb://fitshield_ro:F!t%24h!3lD_Pr0D_ro@ec2-13-204-93-167.ap-south-1.compute.amazonaws.com:17018/?authMechanism=SCRAM-SHA-256&authSource=Fitshield"
client = MongoClient(MONGO_URI)
db = client["Fitshield"]
ErrorDishData = db["ErrorDishData"]


# Function to calculate nutrient values for an ingredient
def get_error_model_dish_list(request):
    error_dish_data = list(ErrorDishData.find({}, {'_id': 0}))
    print("Error Dish Data:", error_dish_data)
    return JsonResponse({'error_dish_data': error_dish_data})

