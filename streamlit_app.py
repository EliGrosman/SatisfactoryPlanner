import streamlit as st
from collections import defaultdict
from typing import List, Tuple
from recipemanager import RecipeManager
from structs import Item, Recipe
import math
st.set_page_config(layout="wide")

def main():
    """
    Main function for the Streamlit application.
    """

    st.title("Satisfactory Planner")
    

    recipe_loader = RecipeManager()
    base_recipes = recipe_loader.get_recipes_by_type("base")
    alt_recipes = recipe_loader.get_recipes_by_type("alternate")

    # --- Layout ---
    input_col, ingredients_col, machines_col = st.columns([0.2, 0.2, 0.2])  # Adjust ratio as needed

    # --- Inputs (Left Column) ---
    with input_col:
        st.markdown("## Outputs")
        num_outputs = st.number_input(
            label="Number of outputs", min_value=0, step=1
        )
        output_items = []
        for i in range(num_outputs):
            out_item_col, out_amnt_col = st.columns([0.75, 0.25])
            out_item_val = out_item_col.selectbox(
                label="Item", options=list(base_recipes.keys()), key=f"out{i}"
            )
            out_amnt_val = out_amnt_col.number_input(
                "Amount (per min)", min_value=1.0, step=1.0, key=f"out{i} {i}"
            )
            output_items.append((out_item_val, out_amnt_val))

        st.markdown("## Alt recipes")
        num_alt_recipes = st.number_input(
            label="Number of alt recipes", min_value=0, step=1
        )
        alt_recipes_selected = []
        for i in range(num_alt_recipes):
            alt_item_val = st.selectbox(
                label="Alt recipe", options=list(alt_recipes.keys()), key=f"alt{i}"
            )
            alt_recipes_selected.append(alt_item_val)

        # --- Calculate Button ---
        if st.button("Calculate"):
            calculate_and_display_results(
                recipe_loader, output_items, alt_recipes_selected, ingredients_col, machines_col
            )  # Pass the output column to the function


def calculate_and_display_results(
    recipe_loader: RecipeManager,
    output_items: List[Tuple[str, float]],
    alt_recipes_selected: List[str],
    ingredients_col: st.container,  # Add ingredients_col as an argument
    machines_col: st.container
) -> None:
    """
    Calculates and displays the required ingredients and machines.
    """

    alt_recipes_dict = {}
    for alt_recipe_name in alt_recipes_selected:
        alt_recipe = recipe_loader.RECIPES[alt_recipe_name]
        for alt_output in alt_recipe.outputs:
            alt_recipes_dict[alt_output.item] = alt_recipe

    all_ingredients = []
    all_machines = []

    for output_item_name, output_amount in output_items:
        item = recipe_loader.RECIPES[output_item_name].outputs[0].item  # Get the Item object
        recipe = alt_recipes_dict.get(item, item.baseRecipes[0])

        ingredients = []
        machines = []
        recipe_loader.get_ingredients(
            item=item,
            amount=output_amount,
            recipe=recipe,
            ingredients=ingredients,
            machines=machines,
            max_depth=6,
            alt_recipes=alt_recipes_dict,
        )

        all_ingredients.extend(ingredients)
        all_machines.extend(machines)

    # Aggregate ingredients
    aggregated_ingredients = defaultdict(float)
    for item, amount in all_ingredients:
            aggregated_ingredients[item] += amount

    base_ingredients = defaultdict(float)
    for item, amount in all_ingredients:
        if(item._is_base_ingredient()):
            base_ingredients[item] += amount

    # Aggregate machines
    aggregated_machines = defaultdict(lambda: (0, ""))
    for machine, usage, recipe in all_machines:
        aggregated_machines[recipe] = (
            aggregated_machines[recipe][0] + usage,
            machine,
        )

    total_machines = defaultdict(lambda: (0, 0))
    for _, (usage, machine) in aggregated_machines.items():
        total_machines[machine] = (
            total_machines[machine][0] + math.ceil(usage),
            total_machines[machine][1] + max(1, math.floor(usage)),
        )

    # --- Sort Results ---
    sorted_ingredients = sorted(
        aggregated_ingredients.items(), key=lambda item: (-item[1], item[0].itemName)
    )  # Sort ingredients by amount (descending) then by name (ascending)

    sorted_base_ingredients = sorted(
        base_ingredients.items(), key=lambda item: (-item[1], item[0].itemName)
    )  # Sort ingredients by amount (descending) then by name (ascending)


    sorted_machines = sorted(
        aggregated_machines.items(),
        key=lambda item: (item[1][1].machineName, item[0].recipeName, item[1][0]),
    )  # Sort machines by machine name, then recipe, then usage

    sorted_total_machines = sorted(
        total_machines.items(), key=lambda item: item[0].machineName
    ) # Sort total machines by machine name

    # --- Display Results (Right Column) ---
    with ingredients_col:
        st.markdown("## Ingredients:")
        
        st.markdown("### Base Ingredients")
        # --- Display Ingredients in a table ---
        ingredients_html = """
        <table>
            <thead>
                <tr>
                    <th>Ingredient</th>
                    <th>Amount</th>
                </tr>
            </thead>
            <tbody>
        """
        for ingredient, amount in sorted_base_ingredients:
            ingredients_html += f"<tr><td>{ingredient.itemName}</td><td>{amount:.2f}</td></tr>"
        ingredients_html += "</tbody></table>"
        st.markdown(ingredients_html, unsafe_allow_html=True)  # Render as HTML


        st.markdown("### All ingredients:")
        
        # --- Display Ingredients in a table ---
        ingredients_html = """
        <table>
            <thead>
                <tr>
                    <th>Ingredient</th>
                    <th>Amount</th>
                </tr>
            </thead>
            <tbody>
        """
        for ingredient, amount in sorted_ingredients:
            ingredients_html += f"<tr><td>{ingredient.itemName}</td><td>{amount:.2f}</td></tr>"
        ingredients_html += "</tbody></table>"
        st.markdown(ingredients_html, unsafe_allow_html=True)  # Render as HTML

    with machines_col:
        st.markdown("## Machines:")

        st.markdown("### Total machines")

        total_machines_html = """
        <table>
            <thead>
                <tr>
                    <th>Machine</th>
                    <th>Total Amount (no overclocking)</th>
                    <th>Total Amount (+1 power cyrstal per recipe)</th>
                </tr>
            </thead>
            <tbody>
        """
        for machine, (total, total_oc) in sorted_total_machines:
            total_machines_html += f"<tr><td>{machine.machineName}</td><td>{total}</td><td>{total_oc}</td></tr>"
        total_machines_html += "</tbody></table>"
        st.markdown(total_machines_html, unsafe_allow_html=True)

        st.markdown("### Machines per recipe:")
    
        # --- Display Machines in a table ---
        machines_html = """
        <table>
            <thead>
                <tr>
                    <th>Machine</th>
                    <th>Recipe</th>
                    <th>Usage</th>
                    <th>Actual Amount (no overclocking)</th>
                    <th>Actual Amount (+1 power crystal)</th>
                </tr>
            </thead>
            <tbody>
        """
        for recipe, (usage, machine) in sorted_machines:
            machines_html += f"<tr><td>{machine.machineName}</td><td>{recipe.recipeName}</td><td>{usage:.2f}</td><td>{math.ceil(usage)}</td><td>{max(1, math.floor(usage))}</td></tr>"
        machines_html += "</tbody></table>"
        st.markdown(machines_html, unsafe_allow_html=True)  # Render as HTML

        



if __name__ == "__main__":
    main()