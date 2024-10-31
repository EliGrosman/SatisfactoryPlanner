import streamlit as st
from collections import defaultdict
from typing import List, Tuple, Dict
from recipe_manager import RecipeManager

recipeManager = RecipeManager()
alt_recipes = recipeManager.get_recipes_by_type("alternate")

input_col, diff_col, out_col = st.columns([0.3, 0.3, 0.3])

with input_col:
    st.markdown("## Input Items")
    num_inputs = st.number_input(
        label="Number of inputs", min_value=0, step=1
    )

    input_items = []
    for i in range(num_inputs):
        in_item_col, in_amnt_col = st.columns([0.75, 0.25])

        in_item_val = in_item_col.selectbox(
            label="Item", options=list(recipeManager.ITEMS.keys()), key=f"in{i}"
        )

        in_amnt_val = in_amnt_col.number_input(
            label="Amount (per min)", min_value=0.0, step=1.0, key=f"in{i} {i}"
        )
        input_items.append((in_item_val, in_amnt_val))

    st.markdown("## Output Items")
    num_inputs = st.number_input(
        label="Number of outputs", min_value=0, step=1
    )

    output_items = []
    for i in range(num_inputs):
        out_item_col, out_min_col, out_max_col = st.columns([0.75, 0.125, 0.125])

        out_item_val = out_item_col.selectbox(
            label="Item", options=list(recipeManager.ITEMS.keys()), key=f"out{i}"
        )

        out_min_val = out_min_col.number_input(
            label="Min", min_value=0.0, step=1.0, key=f"out{i} {i}"
        )

        out_max_val = out_max_col.number_input(
            label="Max", min_value=0.0, step=1.0, key=f"out{i} {i} {i}"
        )
        output_items.append((out_item_val, out_min_val, out_max_val))

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

    with diff_col:
        remaining, needed, output = recipeManager.optimize(input_items, alt_recipes_selected, output_items)
        if output is None:
            st.markdown("## Invalid input")
        else:
            st.markdown("## Inputs")

            st.markdown("### Required Ingredients")
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
            for ingredient, amount in needed.items():
                ingredients_html += f"<tr><td>{ingredient.itemName}</td><td>{amount:.2f}</td></tr>"
            ingredients_html += "</tbody></table>"
            st.markdown(ingredients_html, unsafe_allow_html=True)  # Render as HTML


            st.markdown("### Remaining Items")
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
            for ingredient, amount in remaining.items():
                ingredients_html += f"<tr><td>{ingredient}</td><td>{amount:.2f}</td></tr>"
            ingredients_html += "</tbody></table>"
            st.markdown(ingredients_html, unsafe_allow_html=True)  # Render as HTML

            with out_col:
                st.markdown("## Outputs")
                st.markdown("### Output Items")
                # --- Display Ingredients in a table ---
                ingredients_html = """
                <table>
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for ingredient, amount in output:
                    ingredients_html += f"<tr><td>{ingredient}</td><td>{abs(float(amount)):.2f}</td></tr>"
                ingredients_html += "</tbody></table>"
                st.markdown(ingredients_html, unsafe_allow_html=True)  # Render as HTML