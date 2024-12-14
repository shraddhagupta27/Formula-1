import pandas as pd
import plotly.express as px
from flask import Flask, render_template
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import pandas as pd
import dash  # Importing the dash module explicitly to access callback_context
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import os

# Initialize Flask app
app = Flask(__name__)


# choropleth

# # Load data
circuits = pd.read_csv("data/circuits.csv")
races = pd.read_csv("data/races.csv")
drivers = pd.read_csv("data/drivers.csv")
constructors = pd.read_csv("data/constructors.csv")
results = pd.read_csv("data/results.csv")
file_path = (
    "data/f1_constructor_driver_points_2015_2024.csv"  # Replace with your file path
)
data2 = pd.read_csv(file_path)

# races["year"] = races["year"].astype(int)
circuit_races = pd.merge(circuits, races, on="circuitId")

# Count the number of races hosted by each country each year
race_frequency = (
    circuit_races.groupby(["country", "year"])["raceId"].count().reset_index()
)
race_frequency.rename(columns={"raceId": "race_count"}, inplace=True)

top_countries = race_frequency.sort_values(by="race_count", ascending=False).head(10)

# Calculate cumulative race count for map
top_countries["Cumulative_Race_Count"] = top_countries.groupby("country")[
    "race_count"
].cumsum()
top_countries = top_countries.sort_values(by="year")

# Define the year ranges for cumulative calculation
year_ranges = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]

# Prepare the cumulative table
cumulative_data = []
for year in year_ranges:
    filtered_data = circuit_races[circuit_races["year"] <= year]
    country_race_count = (
        filtered_data.groupby("country").size().reset_index(name="race_count")
    )
    country_race_count["year_range"] = f"{year}"
    cumulative_data.append(country_race_count)

# Concatenate all cumulative data into a single DataFrame
cumulative_table = pd.concat(cumulative_data, ignore_index=True)

# Create the animated choropleth map
choropleth_fig = px.choropleth(
    cumulative_table,
    locations="country",
    locationmode="country names",
    color="race_count",
    animation_frame="year_range",
    title="Expansion of Formula 1 Circuits Over Time",
    color_continuous_scale=px.colors.sequential.Viridis[::-1],
    labels={"race_count": "Number of Races"},
)

choropleth_fig.update_layout(
    # width=1800,  # Adjust the width of the map
    height=700,
    geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
    coloraxis_colorbar=dict(
        title="Number of Races",
        ticks="outside",
        tickvals=[
            0,
            20,
            40,
            60,
            80,
            100,
            120,
        ],  # Customize tick values (adjust as needed)
    ),
)


# bar chart

# Count the number of races for each circuit
race_counts = races.groupby("circuitId").size().reset_index(name="race_count")
# Merge with circuits dataset to get circuit names
circuits_with_counts = pd.merge(
    race_counts, circuits[["circuitId", "name"]], on="circuitId"
)

# Sort by race count and select the top 10 circuits
top_10_circuits = circuits_with_counts.sort_values(
    by="race_count", ascending=False
).head(10)

# Normalize race_count to create a gradient
min_count = top_10_circuits["race_count"].min()
max_count = top_10_circuits["race_count"].max()
top_10_circuits["normalized_color"] = (top_10_circuits["race_count"] - min_count) / (
    max_count - min_count
)

# Create the figure
fig = go.Figure()

# Add scatter trace for the lollipop marker (dot)
fig.add_trace(
    go.Scatter(
        x=top_10_circuits["race_count"],
        y=top_10_circuits["name"],
        mode="markers",
        marker=dict(
            size=10,
            color=top_10_circuits["normalized_color"],
            colorscale="Viridis",  # Colorblind-friendly palette
            cmin=0,
            cmax=1,
            colorbar=dict(title="Race Count"),  # Add a colorbar
        ),
        name="Race Count",
    )
)

# Add bar trace for the lollipop stems
fig.add_trace(
    go.Bar(
        x=top_10_circuits["race_count"],
        y=top_10_circuits["name"],
        orientation="h",  # Horizontal bar
        marker=dict(
            color=top_10_circuits["normalized_color"],
            colorscale="Viridis",  # Colorblind-friendly palette
            cmin=0,
            cmax=1,
        ),
        name="",
    )
)

# Update layout for aesthetics
fig.update_layout(
    title="Top Circuits by Number of Races",
    xaxis_title="Number of Races",
    yaxis_title="Circuit",
    yaxis=dict(categoryorder="total ascending"),  # Order by race count
    showlegend=False,  # Hide legend
    plot_bgcolor="white",  # White background for contrast
    paper_bgcolor="white",  # White paper background
    # width=1800,
    height=700,
)


# treemap

# Merge datasets
race_winners = results[results["positionOrder"] == 1]  # Filter for race winners
race_winners = pd.merge(race_winners, races[["raceId", "year"]], on="raceId")
race_winners = pd.merge(
    race_winners, drivers[["driverId", "forename", "surname"]], on="driverId"
)
race_winners = pd.merge(
    race_winners, constructors[["constructorId", "name"]], on="constructorId"
)
race_winners["driverName"] = race_winners["forename"] + " " + race_winners["surname"]

# Aggregate wins for each constructor
constructor_wins = race_winners.groupby("name")["positionOrder"].count().reset_index()
constructor_wins.rename(columns={"positionOrder": "wins"}, inplace=True)

# Sort by wins and take the top 10 constructors
top_10_constructors = (
    constructor_wins.sort_values(by="wins", ascending=False).head(10)["name"].tolist()
)

# Filter data for the top 10 constructors
filtered_data = race_winners[race_winners["name"].isin(top_10_constructors)]

# Prepare data for treemap
treemap_data = (
    filtered_data.groupby(["name", "driverName"])["positionOrder"]
    .count()
    .reset_index()
    .rename(
        columns={"name": "Constructor", "driverName": "Driver", "positionOrder": "Wins"}
    )
)

# Add total wins for each constructor (needed for grouping in treemap)
constructor_totals = (
    treemap_data.groupby("Constructor")["Wins"]
    .sum()
    .reset_index()
    .rename(columns={"Wins": "Total Wins"})
)
constructor_totals["Driver"] = constructor_totals[
    "Constructor"
]  # Placeholder for grouping
treemap_data = pd.concat([treemap_data, constructor_totals], ignore_index=True)

# Create Treemap
fig2 = px.treemap(
    treemap_data,
    path=["Constructor", "Driver"],  # Drill-down hierarchy
    values="Wins",
    color="Wins",
    color_continuous_scale=px.colors.sequential.Plasma,
    title="Treemap of Constructor Wins and Driver Contributions",
)

fig2.update_layout(
    margin=dict(t=10, l=25, r=25, b=10),  # Adjust margins
    coloraxis_colorbar=dict(title="Wins"),  # Colorbar title
)


# Merge results with drivers, constructors, and races
merged = pd.merge(results, drivers[["driverId", "forename", "surname"]], on="driverId")
merged = pd.merge(merged, constructors[["constructorId", "name"]], on="constructorId")
merged = pd.merge(merged, races[["raceId", "year"]], on="raceId")

# Create full driver name
merged["driverName"] = merged["forename"] + " " + merged["surname"]

# Aggregate to get total races for each constructor
constructor_races = merged.groupby("name")["raceId"].count().reset_index()
constructor_races.rename(
    columns={"name": "constructor", "raceId": "total_races"}, inplace=True
)

# Identify the top 10 constructors by total races
top_10_constructors = (
    constructor_races.sort_values(by="total_races", ascending=False)
    .head(10)["constructor"]
    .tolist()
)

# Filter merged data to include only the top 10 constructors
filtered_merged = merged[merged["name"].isin(top_10_constructors)]


# Filter for race winners (positionOrder = 1)
race_winners = results[results["positionOrder"] == 1]

# Aggregate wins for each constructor
constructor_wins = (
    race_winners.groupby("constructorId")["positionOrder"].count().reset_index()
)
constructor_wins.rename(columns={"positionOrder": "wins"}, inplace=True)

# Merge with constructors to get names
constructor_wins_with_names = pd.merge(
    constructor_wins, constructors[["constructorId", "name"]], on="constructorId"
)

# Sort by wins and take the top 10 constructors
top_10_winners = constructor_wins_with_names.sort_values(
    by="wins", ascending=False
).head(10)

# Filter for race winners
race_winners = results[results["positionOrder"] == 1]

# Aggregate wins for each constructor
constructor_wins = (
    race_winners.groupby("constructorId")["positionOrder"].count().reset_index()
)
constructor_wins.rename(columns={"positionOrder": "wins"}, inplace=True)

# Merge with constructors to get names
constructor_wins_with_names = pd.merge(
    constructor_wins, constructors[["constructorId", "name"]], on="constructorId"
)

# Sort by wins and take the top 10 constructors
top_10_winners = constructor_wins_with_names.sort_values(
    by="wins", ascending=False
).head(10)

# Merge race winners with driver and constructor details
race_winners = pd.merge(
    race_winners, drivers[["driverId", "forename", "surname"]], on="driverId"
)
race_winners = pd.merge(
    race_winners, constructors[["constructorId", "name"]], on="constructorId"
)
race_winners["driverName"] = race_winners["forename"] + " " + race_winners["surname"]

# Initialize Dash app
# app = Dash(__name__)
dash_app = Dash(__name__, server=app, url_base_pathname="/dash/")

# Layout
dash_app.layout = html.Div(
    [
        # html.H1("F1 Constructors and Driver Contributions"),
        dcc.Graph(id="treemap"),
        html.Button(
            "Reset to Constructors",
            id="reset-button",
            n_clicks=0,
            style={"margin-top": "10px"},
        ),
        html.Div(id="selected-constructor", style={"margin-top": "10px"}),
    ]
)


# Callback for dynamic updates
@dash_app.callback(
    Output("treemap", "figure"),
    Output("selected-constructor", "children"),
    [Input("treemap", "clickData"), Input("reset-button", "n_clicks")],
)
def update_treemap(click_data, n_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        # Default view
        fig2 = px.treemap(
            top_10_winners,
            path=["name"],
            values="wins",
            title="Top 10 Constructors by Wins",
            color="wins",
            color_continuous_scale=px.colors.sequential.Plasma,
        )
        return fig2, "Click on a constructor to see driver details."

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "reset-button":
        # Reset view
        fig2 = px.treemap(
            top_10_winners,
            path=["name"],
            values="wins",
            title="Top 10 Constructors by Wins",
            color="wins",
            color_continuous_scale=px.colors.sequential.Plasma,
        )
        return fig2, "Click on a constructor to see driver details."

    if trigger_id == "treemap" and click_data:
        # Drill down to show driver details for the clicked constructor
        selected_constructor = click_data["points"][0]["label"]
        filtered_data = race_winners[race_winners["name"] == selected_constructor]
        driver_data = (
            filtered_data.groupby(["name", "driverName"])["positionOrder"]
            .count()
            .reset_index()
        )
        driver_data.rename(
            columns={"name": "constructor", "positionOrder": "wins"}, inplace=True
        )
        fig2 = px.treemap(
            driver_data,
            path=["constructor", "driverName"],
            values="wins",
            title=f"Driver Contributions for {selected_constructor}",
            color="wins",
            color_continuous_scale=px.colors.sequential.Plasma,
        )
        return fig2, f"Showing details for {selected_constructor}"

    # Default view as fallback
    fig2 = px.treemap(
        top_10_winners,
        path=["name"],
        values="wins",
        title="Top 10 Constructors by Wins",
        color="wins",
        color_continuous_scale=px.colors.sequential.Plasma,
    )
    return fig2, "Click on a constructor to see driver details."


# line

# Step 1: Merge results with races and drivers
driver_performance = pd.merge(results, races, on="raceId")
driver_performance = pd.merge(driver_performance, drivers, on="driverId")

# Step 2: Add columns to identify wins and podium finishes
driver_performance["podium"] = driver_performance["positionOrder"].apply(
    lambda x: 1 if x <= 3 else 0
)
driver_performance["win"] = driver_performance["positionOrder"].apply(
    lambda x: 1 if x == 1 else 0
)

# Step 3: Aggregate total wins for drivers from 2015 onward
active_driver_wins = (
    driver_performance[
        driver_performance["year"] >= 2015
    ]  # Filter data for 2015 onward
    .groupby(["driverId", "surname"], as_index=False)
    .agg(total_wins=("win", "sum"))
    .sort_values(by="total_wins", ascending=False)
    .head(10)  # Select top 10 drivers
)

# Step 4: Filter main dataset for top 10 drivers
top_10_driver_stats = (
    driver_performance[
        driver_performance["driverId"].isin(active_driver_wins["driverId"])
    ]
    .groupby(["driverId", "surname", "year"], as_index=False)
    .agg(
        total_points=("points", "sum"),
        podiums=("podium", "sum"),
        wins=("win", "sum"),
        races_participated=("raceId", "count"),
        win_rate=("win", lambda x: (x.sum() / len(x)) * 100),
    )
)


# Step 5: Create an interactive line chart for wins across seasons
fig3 = px.line(
    top_10_driver_stats,
    x="year",
    y="wins",
    color="surname",
    line_group="driverId",
    title="Top 10 Drivers by Wins Across Seasons",
    labels={"year": "Season", "wins": "Number of Wins", "surname": "Driver"},
    markers=True,
)

# Customize layout
fig3.update_layout(
    template="plotly_white",
    xaxis=dict(title="Season"),
    yaxis=dict(title="Number of Wins"),
    legend_title="Driver",
    hovermode="closest",
    # width=1800,
    height=700,
)


# barr

# Get the list of unique years
years = sorted(data2["Year"].unique())

# Create a figure for the dropdown functionality
fig4 = go.Figure()

# Track the visibility of all traces
trace_visibility = []

# Add traces for each year
for year in years:
    yearly_data = data2[data2["Year"] == year]
    teams = yearly_data["Team"].unique()

    # Add traces for each team
    for team in teams:
        team_data = yearly_data[yearly_data["Team"] == team]
        fig4.add_trace(
            go.Bar(
                x=team_data["Drivers"],
                y=team_data["Points"],
                name=team,
                marker=dict(color=team_data["Colour"].iloc[0]),  # Use team color
                text=team_data["Points"],
                textposition="outside",
                visible=(year == 2018),  # Show only 2018 data by default
            )
        )
        # Track visibility for each year
        trace_visibility.append((team, year))

# Create the dropdown menu
dropdown_buttons = []
for year in years:
    # Create a visibility array for the dropdown
    visibility = [y == year for _, y in trace_visibility]
    dropdown_buttons.append(
        dict(
            label=str(year),
            method="update",
            args=[
                {"visible": visibility},  # Update visibility
                {"title": f"F1 Driver Points - {year}"},  # Update the title
            ],
        )
    )

# Update layout with dropdown
fig4.update_layout(
    updatemenus=[
        dict(
            buttons=dropdown_buttons,
            direction="down",
            showactive=True,
        )
    ],
    title="F1 Driver Points - 2018",
    xaxis_title="Drivers",
    yaxis_title="Points Scored",
    plot_bgcolor="white",
    paper_bgcolor="white",
    barmode="group",  # Grouped bar chart
    legend_title="Teams",  # Set legend title
    # width=1800,  # Adjust the width of the map
    height=700,
)


# Define route for rendering template
@app.route("/")
def index():
    # Embed Plotly choropleth figure
    choropleth_html = choropleth_fig.to_html(full_html=False)

    bar_html = fig.to_html(full_html=False)

    tree_html = fig2.to_html(full_html=False)

    line_html = fig3.to_html(full_html=False)

    barr_html = fig4.to_html(full_html=False)

    return render_template(
        "index.html",
        choropleth_html=choropleth_html,
        bar_html=bar_html,
        tree_html=tree_html,
        line_html=line_html,
        barr_html=barr_html,
    )


# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(debug=True, host='0.0.0.0', port=port)
