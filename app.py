from flask import Flask, render_template, request, redirect, url_for, session
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'

COMMON_EXPENSES = [
    "Rent/Mortgage", "Groceries", "Utilities", "Transportation",
    "Phone", "Internet", "Insurance", "Taxes", "Entertainment", "Dining Out"
]

@app.route("/", methods=["GET", "POST"])
def intro():
    if request.method == "POST":
        income = request.form.get("income")
        session["income"] = float(income)
        return redirect(url_for("expenses"))
    return render_template("intro.html")

@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if request.method == "POST":
        expenses = {}
        for item in COMMON_EXPENSES:
            amount = request.form.get(item)
            if amount:
                expenses[item] = float(amount)

        other_names = request.form.getlist("other_name")
        other_amounts = request.form.getlist("other_amount")
        for name, amount in zip(other_names, other_amounts):
            if name and amount:
                expenses[name] = float(amount)

        session["expenses"] = expenses
        return redirect(url_for("results"))

    return render_template("expenses.html", expenses=COMMON_EXPENSES)

@app.route("/results")
def results():
    income = session.get("income", 0)
    expenses = session.get("expenses", {})

    need_keywords = [
        "Rent", "Mortgage", "Groceries", "Utilities",
        "Transportation", "Phone", "Internet", "Insurance", "Taxes"
    ]
    categorized = {"Needs": 0, "Wants": 0}
    for name, amount in expenses.items():
        if any(keyword.lower() in name.lower() for keyword in need_keywords):
            categorized["Needs"] += amount
        else:
            categorized["Wants"] += amount

    total_expenses = categorized["Needs"] + categorized["Wants"]
    leftover = income - total_expenses

    chart_img = generate_chart(income, categorized)
    return render_template("results.html", income=income, expenses=total_expenses,
                           categorized=categorized, leftover=leftover, chart=chart_img)

@app.route("/recommendations")
def recommendations():
    # Pull session data
    income = session.get("income")
    expenses = session.get("expenses")

    # Redirect to intro if session data is missing
    if income is None or expenses is None or not expenses:
        return redirect(url_for("intro"))

    # Categorize expenses
    need_keywords = [
        "Rent", "Mortgage", "Groceries", "Utilities",
        "Transportation", "Phone", "Internet", "Insurance", "Taxes"
    ]
    
    categorized = {"Needs": 0, "Wants": 0}
    for name, amount in expenses.items():
        if any(keyword.lower() in name.lower() for keyword in need_keywords):
            categorized["Needs"] += amount
        else:
            categorized["Wants"] += amount

    total_expenses = categorized["Needs"] + categorized["Wants"]
    leftover = income - total_expenses

    # Generate recommendations
    recommendations_list = []

    if leftover < 0:
        recommendations_list.append("You are spending more than your income. Consider reducing some expenses.")
    elif leftover < income * 0.1:
        recommendations_list.append("Your leftover is small. Try to save a little more each month.")
    else:
        recommendations_list.append("You have a healthy leftover. Consider saving or investing it.")

    if categorized["Wants"] > income * 0.3:
        recommendations_list.append("You might be spending too much on wants. Try reducing entertainment or dining out.")

    if categorized["Needs"] > income * 0.6:
        recommendations_list.append("Your essential expenses are high. Look for ways to cut costs on necessities.")

    return render_template(
        "recommendations.html",
        income=income,
        categorized=categorized,
        leftover=leftover,
        recommendations=recommendations_list
    )




def generate_chart(income, categorized):

    labels = ['Income', 'Needs', 'Wants', 'Needs + Wants']
    values = [income, categorized['Needs'], categorized['Wants'], categorized['Needs'] + categorized['Wants']]
    colors = ['green', 'orange', 'red', 'blue']

    plt.figure(figsize=(8, 5))

    # Calculate maximum value for y-axis and add padding
    max_value = max(values)
    padding = max_value * 0.15  # 15% headroom
    plt.ylim(0, max_value + padding)

    # Plot bars
    bars = plt.bar(labels, values, color=colors)
    plt.title('Income vs Expenses')
    plt.ylabel('Amount ($)')

    # Add value labels above each bar
    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max_value * 0.02,  # vertical offset from bar
            f"${value:,.0f}",
            ha='center',
            va='bottom',
            fontsize=10,
            fontweight='bold'
        )

    plt.tight_layout()

    # Convert to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return img


if __name__ == "__main__":
    app.run(debug=True)
