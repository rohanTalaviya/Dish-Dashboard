from django.http import JsonResponse
from pymongo import MongoClient

# MongoDB connection
MONGO_URI = "mongodb://Kishan:KishankFitshield@13.235.142.65:27017/?authMechanism=SCRAM-SHA-256&authSource=Fitshield"
client = MongoClient(MONGO_URI)
db = client["Fitshield"]
ModelData = db["ModelData"]
RestroModelData = db["RestroModelData"]

# Function to calculate nutrient values for an ingredient
def get_model_dish_list(request):
    dish_list = list(ModelData.find({}, {'_id': 0, 'dish_name': 1}))
    return JsonResponse({'data_list': dish_list})

def get_restaurant_model_dish_list(request):
    dish_list = list(RestroModelData.find({}, {'_id': 0, 'dish_name': 1}))
    return JsonResponse({'data_list': dish_list})
