from django.http import JsonResponse
from pymongo import MongoClient

# MongoDB connection
MONGO_URI = "mongodb://Kishan:KishankFitshield@ec2-13-233-104-209.ap-south-1.compute.amazonaws.com:27017/?authMechanism=SCRAM-SHA-256&authSource=Fitshield"
client = MongoClient(MONGO_URI)
db = client["Fitshield"]
RestaurantMenuData = db["RestaurantMenuData"]

def get_restaurant_list(request):
    try:
        # Fetch data from MongoDB
        restaurant_list = list(RestaurantMenuData.find({}, {'_id': 1}))

        if not restaurant_list:
            print("No data found in RestaurantMenuData collection.")  # Debugging log

        return JsonResponse({'restaurant_list': restaurant_list})
    except Exception as e:
        print("Error fetching restaurant list:", str(e))  # Debugging log for errors
        return JsonResponse({'error': 'Failed to fetch restaurant list', 'details': str(e)}, status=500)

def get_restaurant_dish_list(request):
    try:
        # Get restaurant ID from request parameters
        restaurant_id = request.GET.get('restaurant_id', None)
        if not restaurant_id:
            return JsonResponse({'error': 'Restaurant ID is required'}, status=400)

        # Fetch data from MongoDB with the specified restaurant ID
        restaurant_dish_list = list(RestaurantMenuData.find({"_id": restaurant_id}, {'_id': 1}))
        print("Fetched restaurant dish list:", restaurant_dish_list)

        if not restaurant_dish_list:
            print(f"No data found for the restaurant ID: {restaurant_id}")

        return JsonResponse({'restaurant_dish_list': restaurant_dish_list})
    except Exception as e:
        print("Error fetching restaurant dish list:", str(e)) 
        return JsonResponse({'error': 'Failed to fetch restaurant dish list', 'details': str(e)}, status=500)

def get_dish_names(request):
    try:
        # Get restaurant ID from request parameters
        restaurant_id = request.GET.get('restaurant_id', None)
        
        if not restaurant_id:
            return JsonResponse({'error': 'Restaurant ID is required'}, status=400)

        # Fetch dish names and not_found_ingredient for the specified restaurant ID
        result = RestaurantMenuData.find_one(
            {"_id": restaurant_id},
            {"menu.dish_name": 1, "menu.not_found_ingredient": 1, "_id": 0}
        )
        
        # Safely extract dish names and not_found_ingredient
        dish_data = [
            {
                "dish_name": dish.get("dish_name"),
                "not_found_ingredient": dish.get("not_found_ingredient")
            }
            for dish in result.get("menu", [])
            if "dish_name" in dish
        ]
        #print("Fetched dish data:", dish_data)

        return JsonResponse({'dish_data': dish_data})
    except Exception as e:
        print("Error fetching dish names:", str(e))  # Debugging log for errors
        return JsonResponse({'error': 'Failed to fetch dish names', 'details': str(e)}, status=500)