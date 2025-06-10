document.addEventListener('DOMContentLoaded', function() {
    
    const urlParams = new URLSearchParams(window.location.search);
    const dishName = urlParams.get('dish_name');
    //console.log('dishName:', dishName);
    const source = urlParams.get('source');
    const restaurantId = urlParams.get('restaurant_id');

    fetch(`/get_dish_details/?dish_name=${encodeURIComponent(dishName)}&source=${encodeURIComponent(source)}&restaurant_id=${encodeURIComponent(restaurantId)}`)
        .then(response => response.json())
        .then(data => {
            const details = data.dish_details;
            console.log('Dish Details:', details);    

            document.getElementById('dishImage').src = details.dish_img_url;
            document.getElementById('dishName').textContent = details.dish_name; 
            document.getElementById('dishDescription').value = details.dish_description;

            document.getElementById('specificCuisine').value = details.cuisine_category.specific_cuisine;
            document.getElementById('continentalRegion').value = details.cuisine_category.continental_region;
            document.getElementById('subcategory').value = details.cuisine_category.subcategory;
            document.getElementById('foodCategory').value = details.food_category;
            document.getElementById('mealCategory').value = details.meal_category.join(', ');
            document.getElementById('courseCategory').value = details.timing_category.join(', ');

            document.getElementById('cookingTime').value = details.cooking_time;
            document.getElementById('cookingTemperature').value = details.cooking_temperature;

            document.getElementById('cookingStyle').value = details.cooking_style || ''; // Populate cooking style

            const cookingSteps = document.getElementById('cookingSteps');
            details.cooking_steps.forEach(step => {
                const li = document.createElement('li');
                const input = document.createElement('input');
                input.type = 'text';
                input.value = step;
                input.style.width = '100%';
                li.appendChild(input);
                cookingSteps.appendChild(li);
            });

            const ingredientsList = document.getElementById('ingredientsList');
            const dbIngredientNames = document.getElementById('dbIngredientNames');

            details.dish_variants.normal.full.ingredients.forEach(ingredient => {
                const ingredientLi = document.createElement('li');
                ingredientLi.style.display = 'flex';
                ingredientLi.style.justifyContent = 'space-between';
                ingredientLi.style.marginBottom = '10px';

                const nameInput = document.createElement('input');
                nameInput.type = 'text';
                nameInput.value = ingredient.name;
                nameInput.style.flex = '1'; // Reduced from '2' to '1'
                nameInput.style.maxWidth = '80px'; // Add a max width for further control
                nameInput.className = 'ingredient-name';

                const quantityInput = document.createElement('input');
                quantityInput.type = 'text';
                quantityInput.value = ingredient.quantity;
                quantityInput.style.flex = '0.5'; // Reduced flex
                quantityInput.style.maxWidth = '80px'; // Added max-width
                quantityInput.className = 'ingredient-quantity';

                const unitSelect = document.createElement('select'); // Changed to dropdown
                unitSelect.style.flex = '0.5'; // Reduced flex
                unitSelect.style.maxWidth = '80px'; // Added max-width
                unitSelect.className = 'ingredient-unit';
                ['g', 'ml'].forEach(optionValue => {
                    const option = document.createElement('option');
                    option.value = optionValue;
                    option.textContent = optionValue;
                    if (optionValue === ingredient.unit) option.selected = true;
                    unitSelect.appendChild(option);
                });

                const descriptionInput = document.createElement('input');
                descriptionInput.type = 'text';
                descriptionInput.value = ingredient.description;
                descriptionInput.style.flex = '1';
                descriptionInput.className = 'ingredient-description';

                const removeButton = document.createElement('button');
                removeButton.innerHTML = '&times;'; 
                removeButton.className = 'small-btn';
                removeButton.style.flex = '0.2'; 
                removeButton.style.padding = '2px'; 
                removeButton.style.fontSize = '0.7em';
                removeButton.onclick = () => {
                    const index = Array.from(ingredientsList.children).indexOf(ingredientLi);
                    ingredientLi.remove();
                    if (dbIngredientNames.children[index]) {
                        dbIngredientNames.children[index].remove();
                    }
                };

                ingredientLi.appendChild(nameInput);
                ingredientLi.appendChild(quantityInput);
                ingredientLi.appendChild(unitSelect); // Append dropdown
                ingredientLi.appendChild(descriptionInput);
                ingredientLi.appendChild(removeButton);
                ingredientsList.appendChild(ingredientLi);

                const dbIngredientLi = document.createElement('li');
                dbIngredientLi.style.display = 'flex';
                dbIngredientLi.style.paddingTop = '17px';
                dbIngredientLi.style.paddingBottom = '18px';

                const dbIngredientText = document.createElement('span');
                dbIngredientText.textContent = ingredient.db_ingredient_name || 'N/A';
                dbIngredientText.style.flex = '1';
                if (ingredient.db_ingredient_name.includes("No match")) {
                    dbIngredientText.style.color = 'red';
                    dbIngredientText.style.fontWeight = 'bold';
                }

                dbIngredientLi.appendChild(dbIngredientText);
                dbIngredientNames.appendChild(dbIngredientLi);
            });

            const nutrientsList = document.getElementById('nutrientsList');
            details.dish_variants.normal.full.nutrients.forEach(nutrient => {
                const li = document.createElement('li');
                li.innerHTML = `<b>${nutrient.name}:</b> ${nutrient.quantity}${nutrient.unit}`;
                nutrientsList.appendChild(li);
            });

            document.getElementById('distributedMacros').textContent = Object.entries(details.distributed_percentage)
                .map(([key, value]) => `${key.charAt(0).toUpperCase() + key.slice(1)}: ${value}`)
                .join(', ');

            document.getElementById('foodClaims').textContent = details.food_claims.join(', ');

            const toppingsList = document.getElementById('toppingsList');
            toppingsList.innerHTML = '';

            // Populate toppings with separate inputs for name and price
            (details.toppings?.length)
                ? details.toppings.forEach(topping => {
                    const li = document.createElement('li');
                    li.style.display = 'flex';
                    li.style.gap = '10px';
                    li.style.marginBottom = '10px';

                    const nameInput = document.createElement('input');
                    nameInput.type = 'text';
                    nameInput.value = topping.name;
                    nameInput.placeholder = 'Topping Name';
                    nameInput.style.flex = '2';

                    const priceInput = document.createElement('input');
                    priceInput.type = 'number';
                    priceInput.value = topping.price;
                    priceInput.placeholder = 'Price';
                    priceInput.style.flex = '1';

                    const removeButton = document.createElement('button');
                    removeButton.innerHTML = '&times;';
                    removeButton.className = 'small-btn';
                    removeButton.onclick = () => li.remove();

                    li.appendChild(nameInput);
                    li.appendChild(priceInput);
                    li.appendChild(removeButton);
                    toppingsList.appendChild(li);
                })
                : toppingsList.appendChild(Object.assign(document.createElement('li'), { textContent: 'No toppings available' }));

            const complementaryDishesInput = document.getElementById('complementaryDishesInput');
            const selectedComplementaryDishes = document.getElementById('selectedComplementaryDishes');
            const complementaryDishesList = details.complementary_dishes || [];

            // Populate selected complementary dishes as tags
            function renderSelectedComplementaryDishes() {
                selectedComplementaryDishes.innerHTML = '';
                complementaryDishesList.forEach(dish => {
                    const span = document.createElement('span');
                    span.textContent = dish;
                    span.className = 'badge';
                    span.style.marginRight = '5px';
                    span.style.cursor = 'pointer';
                    span.onclick = () => {
                        complementaryDishesList.splice(complementaryDishesList.indexOf(dish), 1);
                        renderSelectedComplementaryDishes();
                    };
                    selectedComplementaryDishes.appendChild(span);
                });
            }

            // Add complementary dish to the list when Enter is pressed
            complementaryDishesInput.addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    const inputValue = complementaryDishesInput.value.trim();
                    if (inputValue && !complementaryDishesList.includes(inputValue)) {
                        complementaryDishesList.push(inputValue);
                        renderSelectedComplementaryDishes();
                    }
                    complementaryDishesInput.value = ''; // Clear input field
                }
            });

            // Initialize selected complementary dishes
            renderSelectedComplementaryDishes();

            const allergicContent = document.getElementById('allergicContent');
            const selectedAllergens = document.getElementById('selectedAllergens');
            const allergens = details.allergic_content;

            function renderSelectedAllergens() {
                selectedAllergens.innerHTML = '';
                allergens.forEach(allergen => {
                    const span = document.createElement('span');
                    span.textContent = allergen;
                    span.className = 'badge';
                    span.style.marginRight = '5px';
                    span.style.cursor = 'pointer';
                    span.onclick = () => {
                        allergens.splice(allergens.indexOf(allergen), 1);
                        renderSelectedAllergens();
                    };
                    selectedAllergens.appendChild(span);
                });
            }

            allergicContent.addEventListener('change', function() {
                const selectedValue = allergicContent.value;
                if (selectedValue && !allergens.includes(selectedValue)) {
                    allergens.push(selectedValue);
                    renderSelectedAllergens();
                }
                allergicContent.value = '';
            });

            renderSelectedAllergens();

            const timingCategory = document.getElementById('timingCategory');
            const selectedTimingCategories = document.getElementById('selectedTimingCategories');
            const timingCategories = details.timing_category || [];

            // Populate selected timing categories as tags
            function renderSelectedTimingCategories() {
                selectedTimingCategories.innerHTML = '';
                timingCategories.forEach(category => {
                    const span = document.createElement('span');
                    span.textContent = category;
                    span.className = 'badge';
                    span.style.marginRight = '5px';
                    span.style.cursor = 'pointer';
                    span.onclick = () => {
                        timingCategories.splice(timingCategories.indexOf(category), 1);
                        renderSelectedTimingCategories();
                    };
                    selectedTimingCategories.appendChild(span);
                });
            }

            // Add timing category to the list when selected
            timingCategory.addEventListener('change', function() {
                const selectedValue = timingCategory.value;
                if (selectedValue && !timingCategories.includes(selectedValue)) {
                    timingCategories.push(selectedValue);
                    renderSelectedTimingCategories();
                }
                timingCategory.value = ''; // Reset dropdown
            });

            // Initialize selected timing categories
            renderSelectedTimingCategories();

            const cookingMethod = document.getElementById('cookingMethod');
            const selectedCookingMethods = document.getElementById('selectedCookingMethods');
            const cookingStyle = document.getElementById('cookingStyle'); // Reference to cooking style dropdown
            const cookingMethods = details.cooking_method || [];

            // Populate selected cooking methods as tags
            function renderSelectedCookingMethods() {
                selectedCookingMethods.innerHTML = '';
                cookingStyle.innerHTML = ''; // Clear cooking style dropdown
                cookingMethods.forEach(method => {
                    const span = document.createElement('span');
                    span.textContent = method;
                    span.className = 'badge';
                    span.style.marginRight = '5px';
                    span.style.cursor = 'pointer';
                    span.onclick = () => {
                        cookingMethods.splice(cookingMethods.indexOf(method), 1);
                        renderSelectedCookingMethods();
                    };
                    selectedCookingMethods.appendChild(span);

                    // Add method to cooking style dropdown
                    const option = document.createElement('option');
                    option.value = method;
                    option.textContent = method;
                    cookingStyle.appendChild(option);
                });
            }

            // Add cooking method to the list when selected
            cookingMethod.addEventListener('change', function() {
                const selectedValue = cookingMethod.value;
                if (selectedValue && !cookingMethods.includes(selectedValue)) {
                    cookingMethods.push(selectedValue);
                    renderSelectedCookingMethods();
                }
                cookingMethod.value = ''; // Reset dropdown
            });

            // Initialize selected cooking methods
            renderSelectedCookingMethods();

            // Populate price
            document.getElementById('dishPrice').value = details.price || 0;

            // Set the "Dish Approve" radio button based on is_verified
            const dishApproveRadio = document.getElementById('dishApproveRadio');
            if (details.is_verified === true) {
                dishApproveRadio.checked = true;
            } else {
                dishApproveRadio.checked = false;
            }

            // Add event listener for the "Run Model" button
            document.getElementById('runModel').addEventListener('click', function() {
                const urlParams = new URLSearchParams(window.location.search);
                const dishName = document.getElementById('dishName').textContent.trim();
                const restaurantId = urlParams.get('restaurant_id');
                const dishId = details._id;


                if (!dishName) {
                    alert('Dish name is missing. Please check the dish details.');
                    return;
                }

                // Collect ingredients data
                const ingredients = Array.from(document.getElementById('ingredientsList').children).map(ingredientLi => ({
                    name: ingredientLi.querySelector('.ingredient-name').value,
                    quantity: ingredientLi.querySelector('.ingredient-quantity').value,
                    unit: ingredientLi.querySelector('.ingredient-unit').value,
                    description: ingredientLi.querySelector('.ingredient-description').value,
                }));
                
                // Construct the payload
                const payload = {
                    dishId: dishId,
                    restaurant_id: restaurantId,
                    dish_name : dishName,
                    ingredients: ingredients,
                    origin_ingredient: data.dish_details.dish_variants.normal.full.ingredients,
                    cooking_style: document.getElementById('cookingStyle').value,
                };

                // Log the payload for debugging
                console.log('Payload being sent to Run Model API:', payload);

                // Call the "run_model" API
                fetch('/run_model/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('API Response:', data);
                    alert('Run Model API called successfully!');
                })
                .catch(error => {
                    console.error('Error calling Run Model API:', error);
                    alert('An error occurred while calling the Run Model API.');
                });
            });

            const addIngredientButton = document.getElementById('addIngredient');

            // Function to create a new ingredient row
            function createIngredientRow(name = '', quantity = '', unit = '', description = '') {
                const ingredientLi = document.createElement('li');
                ingredientLi.style.display = 'flex';
                ingredientLi.style.justifyContent = 'space-between';
                ingredientLi.style.marginBottom = '10px';

                const nameInput = document.createElement('input');
                nameInput.type = 'text';
                nameInput.value = name;
                nameInput.placeholder = 'Name';
                nameInput.style.flex = '2'; 
                nameInput.style.maxWidth = '200px';
                nameInput.className = 'ingredient-name';

                const suggestionBox = document.createElement('ul');
                suggestionBox.style.position = 'absolute';
                suggestionBox.style.background = '#fff';
                suggestionBox.style.border = '1px solid #ccc';
                suggestionBox.style.listStyle = 'none';
                suggestionBox.style.padding = '5px';
                suggestionBox.style.margin = '0';
                suggestionBox.style.display = 'none';
                suggestionBox.style.zIndex = '1000';

                nameInput.addEventListener('input', function () {
                    const partialName = nameInput.value.trim();
                    if (partialName.length > 1) {
                        fetchIngredientSuggestions(partialName, suggestions => {
                            suggestionBox.innerHTML = '';
                            if (suggestions.length > 0) {
                                suggestions.forEach(suggestion => {
                                    const suggestionItem = document.createElement('li');
                                    suggestionItem.textContent = suggestion;
                                    suggestionItem.style.cursor = 'pointer';
                                    suggestionItem.style.padding = '8px 12px'; // Improved padding
                                    suggestionItem.style.borderBottom = '1px solid #ddd'; // Add separator
                                    suggestionItem.style.backgroundColor = '#fff'; // White background
                                    suggestionItem.style.color = '#333'; // Dark text
                                    suggestionItem.addEventListener('mouseover', () => {
                                        suggestionItem.style.backgroundColor = '#f0f0f0'; // Highlight on hover
                                    });
                                    suggestionItem.addEventListener('mouseout', () => {
                                        suggestionItem.style.backgroundColor = '#fff'; // Reset background
                                    });
                                    suggestionItem.addEventListener('click', function () {
                                        nameInput.value = suggestion;
                                        suggestionBox.style.display = 'none';
                                    });
                                    suggestionBox.appendChild(suggestionItem);
                                });
                                suggestionBox.style.display = 'block';
                            } else {
                                suggestionBox.style.display = 'none';
                            }
                        });
                    } else {
                        suggestionBox.style.display = 'none';
                    }
                });

                nameInput.addEventListener('blur', function () {
                    setTimeout(() => {
                        suggestionBox.style.display = 'none';
                    }, 200);
                });

                const quantityInput = document.createElement('input');
                quantityInput.type = 'text';
                quantityInput.value = quantity;
                quantityInput.placeholder = 'Quantity';
                quantityInput.style.flex = '0.5';
                quantityInput.style.maxWidth = '80px';
                quantityInput.className = 'ingredient-quantity';

                const unitSelect = document.createElement('select');
                unitSelect.style.flex = '0.5';
                unitSelect.style.maxWidth = '80px';
                unitSelect.className = 'ingredient-unit';
                ['g', 'ml'].forEach(optionValue => {
                    const option = document.createElement('option');
                    option.value = optionValue;
                    option.textContent = optionValue;
                    if (optionValue === unit) option.selected = true;
                    unitSelect.appendChild(option);
                });

                const descriptionInput = document.createElement('input');
                descriptionInput.type = 'text';
                descriptionInput.value = description;
                descriptionInput.placeholder = 'Description';
                descriptionInput.style.flex = '1';
                descriptionInput.className = 'ingredient-description';

                const removeButton = document.createElement('button');
                removeButton.innerHTML = '&times;'; 
                removeButton.className = 'small-btn';
                removeButton.style.flex = '0.2'; 
                removeButton.style.padding = '2px'; 
                removeButton.style.fontSize = '0.9em'; 
                removeButton.onclick = () => {
                    const index = Array.from(ingredientsList.children).indexOf(ingredientLi);
                    ingredientLi.remove();
                    if (dbIngredientNames.children[index]) {
                        dbIngredientNames.children[index].remove();
                    }
                };

                ingredientLi.appendChild(nameInput);
                ingredientLi.appendChild(suggestionBox);
                ingredientLi.appendChild(quantityInput);
                ingredientLi.appendChild(unitSelect); // Append dropdown
                ingredientLi.appendChild(descriptionInput);
                ingredientLi.appendChild(removeButton);
                ingredientsList.appendChild(ingredientLi);
            }

            // Add event listener to the "Add Ingredient" button
            addIngredientButton.addEventListener('click', function() {
                createIngredientRow();
            });

            // Remove redundant population of ingredients list
        })
        .catch(error => {
            console.error('Error fetching dish details:', error);
            alert('An error occurred while fetching dish details.');
        });

    // Add event listener for the "Verify Data" button INSIDE DOMContentLoaded
    document.getElementById('verifyData').addEventListener('click', function () {
        console.log('Verify Data button clicked');
        const urlParams = new URLSearchParams(window.location.search);
        const dishName = document.getElementById('dishName').textContent.trim();
        const source = urlParams.get('source');
        const restaurantId = urlParams.get('restaurant_id');
        const resultDiv = document.getElementById('verifyDataResult');
        resultDiv.textContent = 'Verifying...';

        fetch(`/verify_dish_data/?dish_name=${encodeURIComponent(dishName)}&source=${encodeURIComponent(source)}&restaurant_id=${encodeURIComponent(restaurantId)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Format the comparison result as HTML
                    let html = '<b>Nutrient Comparison:</b><br><table style="width:100%;color:#fff;"><tr><th>Nutrient</th><th>System</th><th>Nutritionix</th><th>Difference</th></tr>';
                    data.comparison.forEach(row => {
                        html += `<tr>
                            <td>${row.nutrient}</td>
                            <td>${row.system_value} ${row.unit}</td>
                            <td>${row.nutritionix_value} ${row.unit}</td>
                            <td>${row.difference} ${row.unit}</td>
                        </tr>`;
                    });
                    html += '</table>';
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.textContent = data.error || 'Verification failed.';
                }
            })
            .catch(err => {
                resultDiv.textContent = 'Error verifying data.';
            });
    });

});

document.getElementById('updateAllFields').addEventListener('click', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const source = urlParams.get('source');
    const restaurantId = urlParams.get('restaurant_id');
    const dishName = document.getElementById('dishName').textContent.trim(); // Ensure dishName is retrieved correctly

    if (!dishName) {
        alert('Dish name is missing. Please check the dish details.');
        console.error('Dish name is missing in the payload.');
        return;
    }

    const toppingsList = document.getElementById('toppingsList');
    const toppings = Array.from(toppingsList.children)
        .filter(toppingLi => toppingLi.querySelector('input[placeholder="Topping Name"]')) // Ensure input exists
        .map(toppingLi => ({
            name: toppingLi.querySelector('input[placeholder="Topping Name"]').value,
            price: parseFloat(toppingLi.querySelector('input[placeholder="Price"]').value) || 0,
        }));

    const updates = {
        'dish_description': document.getElementById('dishDescription').value,
        'cuisine_category.continental_region': document.getElementById('continentalRegion').value,
        'cuisine_category.specific_cuisine': document.getElementById('specificCuisine').value,
        'cuisine_category.subcategory': document.getElementById('subcategory').value,
        'food_category': document.getElementById('foodCategory').value,
        'meal_category': document.getElementById('mealCategory').value.split(',').map(item => item.trim()),
        'timing_category': Array.from(document.getElementById('selectedTimingCategories').children).map(tag => tag.textContent),
        'cooking_method': Array.from(document.getElementById('selectedCookingMethods').children).map(tag => tag.textContent),
        'cooking_time': document.getElementById('cookingTime').value,
        'cooking_temperature': document.getElementById('cookingTemperature').value,
        'allergic_content': Array.from(document.getElementById('selectedAllergens').children).map(tag => tag.textContent),
        'complementary_dishes': Array.from(document.getElementById('selectedComplementaryDishes').children).map(tag => tag.textContent),
        'cooking_style': document.getElementById('cookingStyle').value,
        'toppings': toppings,
        'price': parseFloat(document.getElementById('dishPrice').value) || 0,
    };

    // Add is_verified if radio is checked
    if (document.getElementById('dishApproveRadio').checked) {
        updates['is_verified'] = true;
    }

    const payload = {
        dish_name: dishName, // Ensure dish_name is included in the payload
        updates: updates,
        source: source,
        restaurant_id: restaurantId
    };

    // Log the payload for debugging
    console.log('Payload being sent:', payload);

    fetch('/update_dish_fields/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Dish fields updated successfully!');
        } else {
            alert('Failed to update dish fields: ' + (data.error || data.message));
        }
    })
    .catch(error => {
        console.error('Error updating dish fields:', error);
        alert('An error occurred while updating dish fields.');
    });
});

// Add event listener for the "Add Topping" button
document.getElementById('addTopping').addEventListener('click', function () {
    const toppingsList = document.getElementById('toppingsList');

    const li = document.createElement('li');
    li.style.display = 'flex';
    li.style.gap = '10px';
    li.style.marginBottom = '10px';

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.placeholder = 'Topping Name';
    nameInput.style.flex = '2';

    const priceInput = document.createElement('input');
    priceInput.type = 'number';
    priceInput.placeholder = 'Price';
    priceInput.style.flex = '1';

    const removeButton = document.createElement('button');
    removeButton.innerHTML = '&times;';
    removeButton.className = 'small-btn';
    removeButton.onclick = () => li.remove();

    li.appendChild(nameInput);
    li.appendChild(priceInput);
    li.appendChild(removeButton);
    toppingsList.appendChild(li);
});

function fetchIngredientSuggestions(partialName, callback) {
    fetch(`/suggest_ingredient_name/?partial_name=${encodeURIComponent(partialName)}`)
        .then(response => response.json())
        .then(data => {
            callback(data.suggestions || []);
        })
        .catch(error => {
            console.error('Error fetching ingredient suggestions:', error);
            callback([]);
        });
}

function createIngredientRow(name = '', quantity = '', unit = '', description = '') {
    const ingredientLi = document.createElement('li');
    ingredientLi.style.display = 'flex';
    ingredientLi.style.justifyContent = 'space-between';
    ingredientLi.style.marginBottom = '10px';

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.value = name;
    nameInput.placeholder = 'Name';
    nameInput.style.flex = '2';
    nameInput.className = 'ingredient-name';

    const suggestionBox = document.createElement('ul');
    suggestionBox.style.position = 'absolute';
    suggestionBox.style.background = '#fff';
    suggestionBox.style.border = '1px solid #ccc';
    suggestionBox.style.listStyle = 'none';
    suggestionBox.style.padding = '5px';
    suggestionBox.style.margin = '0';
    suggestionBox.style.display = 'none';
    suggestionBox.style.zIndex = '1000';

    nameInput.addEventListener('input', function () {
        const partialName = nameInput.value.trim();
        if (partialName.length > 1) {
            fetchIngredientSuggestions(partialName, suggestions => {
                suggestionBox.innerHTML = '';
                if (suggestions.length > 0) {
                    suggestions.forEach(suggestion => {
                        const suggestionItem = document.createElement('li');
                        suggestionItem.textContent = suggestion;
                        suggestionItem.style.cursor = 'pointer';
                        suggestionItem.style.padding = '8px 12px'; 
                        suggestionItem.style.borderBottom = '1px solid #ddd'; 
                        suggestionItem.style.backgroundColor = '#fff'; 
                        suggestionItem.style.color = '#333'; 
                        suggestionItem.addEventListener('mouseover', () => {
                            suggestionItem.style.backgroundColor = '#f0f0f0';
                        });
                        suggestionItem.addEventListener('mouseout', () => {
                            suggestionItem.style.backgroundColor = '#fff'; 
                        });
                        suggestionItem.addEventListener('click', function () {
                            nameInput.value = suggestion;
                            suggestionBox.style.display = 'none';
                        });
                        suggestionBox.appendChild(suggestionItem);
                    });
                    suggestionBox.style.display = 'block';
                } else {
                    suggestionBox.style.display = 'none';
                }
            });
        } else {
            suggestionBox.style.display = 'none';
        }
    });

    nameInput.addEventListener('blur', function () {
        setTimeout(() => {
            suggestionBox.style.display = 'none';
        }, 200);
    });

    const quantityInput = document.createElement('input');
    quantityInput.type = 'text';
    quantityInput.value = quantity;
    quantityInput.placeholder = 'Quantity';
    quantityInput.style.flex = '0.5';
    quantityInput.style.maxWidth = '80px';
    quantityInput.className = 'ingredient-quantity';

    const unitSelect = document.createElement('select');
    unitSelect.style.flex = '0.5';
    unitSelect.style.maxWidth = '80px';
    unitSelect.className = 'ingredient-unit';
    ['g', 'ml'].forEach(optionValue => {
        const option = document.createElement('option');
        option.value = optionValue;
        option.textContent = optionValue;
        if (optionValue === unit) option.selected = true;
        unitSelect.appendChild(option);
    });

    const descriptionInput = document.createElement('input');
    descriptionInput.type = 'text';
    descriptionInput.value = description;
    descriptionInput.placeholder = 'Description';
    descriptionInput.style.flex = '1';
    descriptionInput.className = 'ingredient-description';

    const removeButton = document.createElement('button');
    removeButton.innerHTML = '&times;';
    removeButton.className = 'small-btn';
    removeButton.style.flex = '0.2';
    removeButton.onclick = () => ingredientLi.remove();

    ingredientLi.appendChild(nameInput);
    ingredientLi.appendChild(suggestionBox);
    ingredientLi.appendChild(quantityInput);
    ingredientLi.appendChild(unitSelect);
    ingredientLi.appendChild(descriptionInput);
    ingredientLi.appendChild(removeButton);
    document.getElementById('ingredientsList').appendChild(ingredientLi);
}

document.getElementById('verifyData').addEventListener('click', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const dishName = document.getElementById('dishName').textContent.trim();
    const source = urlParams.get('source');
    const restaurantId = urlParams.get('restaurant_id');
    const resultDiv = document.getElementById('verifyDataResult');
    resultDiv.textContent = 'Verifying...';

    fetch(`/verify_dish_data/?dish_name=${encodeURIComponent(dishName)}&source=${encodeURIComponent(source)}&restaurant_id=${encodeURIComponent(restaurantId)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Format the comparison result as HTML
                let html = '<b>Nutrient Comparison:</b><br><table style="width:100%;color:#fff;"><tr><th>Nutrient</th><th>System</th><th>Nutritionix</th><th>Difference</th></tr>';
                data.comparison.forEach(row => {
                    html += `<tr>
                        <td>${row.nutrient}</td>
                        <td>${row.system_value} ${row.unit}</td>
                        <td>${row.nutritionix_value} ${row.unit}</td>
                        <td>${row.difference} ${row.unit}</td>
                    </tr>`;
                });
                html += '</table>';
                resultDiv.innerHTML = html;
            } else {
                resultDiv.textContent = data.error || 'Verification failed.';
            }
        })
        .catch(err => {
            resultDiv.textContent = 'Error verifying data.';
        });
});
