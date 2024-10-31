import streamlit as st
from collections import defaultdict
from typing import List, Tuple
from recipe_manager import RecipeManager
from scipy.optimize import linprog

def get_diff(recipeManager: RecipeManager, items: List[Tuple[str, float]], alt_recipes: List[str], output_items: List[str]):
        if len(items) == 0 or len(output_items) == 0:
             return None, None, None
        output_ings = defaultdict(lambda: defaultdict(1))
        all_base_items = []
        all_items = []
        max_outputs = [v for i, v in output_items]
        for output_item, _ in output_items:
                aggregated_ingredients, out_base_items,   _, _ = recipeManager.calculate_and_display_results([(output_item, 1)], alt_recipes)
                output_ings[output_item] = out_base_items
                all_items.extend(aggregated_ingredients.keys())
                all_base_items.extend(out_base_items.keys())
        all_base_items = set(all_base_items)

        # inputs = [(i[0], i[1]) for i in items if recipeManager.ITEMS[i[0]] in all_items]
        base_items = [(i[0], i[1]) for i in items if recipeManager.ITEMS[i[0]]._is_base_ingredient()]
        non_base_items = [(i[0], i[1]) for i in items if not recipeManager.ITEMS[i[0]]._is_base_ingredient()]

        _, base_ings,          _, _ = recipeManager.calculate_and_display_results(base_items, alt_recipes)
        _, non_base_base_ings, _, _ = recipeManager.calculate_and_display_results(non_base_items, alt_recipes)
        coeffs = {}

        for out_item in output_ings.keys():
                coeffs[out_item] = [output_ings[out_item].get(item, 0) for item in all_base_items] 

        input_amounts = []
        for key in all_base_items:
                base_ings.setdefault(key, 0)
                non_base_base_ings.setdefault(key, 0)

                input_amounts.append(base_ings[key] + non_base_base_ings[key])

        q = []
        modified_inputs = input_amounts.copy()
        for item, rates in coeffs.items():
            qs = [x_j / max(1e-10,a_ij) for x_j, a_ij in zip(input_amounts, rates)]
            q_i = min([x for x in qs if x > 0])

            for i in range(len(input_amounts)):
                if modified_inputs[i] == 0:
                    modified_inputs[i] = rates[i] * q_i
            q.append(q_i)


        # Objective function: Maximize q_1 + q_2 + ... + q_n
        c = [-1] * len(coeffs)  # Negate for maximization

        # Inequality constraints: a_{1j}q_1 + a_{2j}q_2 + ... + a_{nj}q_n <= x_j for all j
        A_ub = []
        b_ub = []
        for j, x_j in enumerate(modified_inputs):
            row = [coeffs[item][j] for item in coeffs]
            A_ub.append(row)
            b_ub.append(x_j)

        # Add constraints for q_i >= min_output for all i
        for i in range(len(coeffs)):
            row = [0] * len(coeffs)
            row[i] = -1  # Coefficient for q_i
            A_ub.append(row)
            b_ub.append(max_outputs[i]) 

        # Bounds: q_i >= 0 for all i
        bounds = [(0, None) for _ in range(len(coeffs))]

        # Solve the linear program
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

        # Extract the optimal q_i values
        optimal_outputs = result.x
        if optimal_outputs is None:
             return [], [], None
        
        output = dict(zip([x[0] for x in output_items], optimal_outputs.tolist()))
        output = [(k, v) for k, v in output.items()]
    
        _, output_base_ings,   _, _ = recipeManager.calculate_and_display_results(output, alt_recipes)
        
        diff = {}
        for item in base_ings:
                diff[item] = base_ings[item] - output_base_ings[item]
        
        remaining = {k: v for k, v in diff.items() if v >= 0}
        needed = {k: -v for k, v in diff.items() if v < 0}

        return remaining, needed, output

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
        out_item_col, out_min_col = st.columns([0.75, 0.25])

        out_item_val = out_item_col.selectbox(
            label="Item", options=list(recipeManager.ITEMS.keys()), key=f"out{i}"
        )

        out_min_val = out_min_col.number_input(
            label="Maximum amount", min_value=0.0, step=1.0, key=f"out{i} {i}"
        )
        output_items.append((out_item_val, out_min_val))

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
        remaining, needed, output = get_diff(recipeManager, input_items, alt_recipes_selected, output_items)
        if output is None:
            st.markdown("## Not possible")
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
                ingredients_html += f"<tr><td>{ingredient.itemName}</td><td>{amount:.2f}</td></tr>"
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