import streamlit as st
from recipeLoader import RecipeLoader
from recipe import ITEMS

recipyLoader = RecipeLoader()
baseRecipes = recipyLoader.getRecipyByType("base")
altRecipes = recipyLoader.getRecipyByType("alternate")


st.title("Satisfactory Planner")


def run():
    alt_recipes = {}

    all_ings = []
    all_machs = []

    for alt_recipy_name in alt_recipes_selected:
        alt_recipy = recipyLoader.RECIPES[alt_recipy_name]

        for alt_out in alt_recipy.outputs:
            alt_recipes[alt_out[0]] = alt_recipy

    for output_item, output_amount in output_items:  
        item = ITEMS[output_item]
        recipe = item.baseRecipes[0]

        if item in alt_recipes.keys():
            recipe = alt_recipes[item]

        ings = []
        machs = []
        recipyLoader.get_ings(item, output_amount, recipe, ings, machs, maxL=6, alt_recipes=alt_recipes)

        all_ings = all_ings + ings
        all_machs = all_machs + machs

    ingredients = {}
    for ing in all_ings:
        if ing[0] not in ingredients.keys():
            ingredients[ing[0]] = 0

        ingredients[ing[0]] = ingredients[ing[0]] + ing[1]


    machines = {}
    for mach in all_machs:
        if mach[2] not in machines.keys():
            machines[mach[2]] = (0, mach[0])

        machines[mach[2]] = (machines[mach[2]][0] + mach[1], machines[mach[2]][1])

    st.markdown("## Ingredients:")  # Display the collected data
    st.write(ingredients)

    st.markdown("## Machines:")  # Display the collected data
    st.write(machines)

st.markdown("# Outputs")
with st.container():
    ncol = st.number_input(label="Number of outputs", min_value=0, step=1)
    output_items = []
    for i in range(ncol):
        out_item, out_amnt = st.columns([0.75, 0.25])
        out_item_val = out_item.selectbox(label="Item", options=list(baseRecipes.keys()), key=f"out{i}")
        out_amnt_val = out_amnt.number_input("Amount", min_value=1.0, step=1.0, key=f"out{i} {i}")
        output_items.append((out_item_val, out_amnt_val))

st.markdown("# Alt recipes")
with st.container():
    ncol = st.number_input(label="Number of alt recipes", min_value=0, step=1)
    alt_recipes_selected = [] 
    for i in range(ncol):
        alt_item_val = st.selectbox(label="Alt recipe", options=list(altRecipes.keys()), key=f"alt{i}")
        alt_recipes_selected.append(alt_item_val)


Submit = st.button("Go", on_click=run)


   







