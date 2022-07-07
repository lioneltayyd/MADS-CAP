# %%
# Python modules. 
import numpy as np 
import pandas as pd 
import altair as alt 
import umap.plot 
from matplotlib import pyplot as plt 
from scipy.cluster.hierarchy import dendrogram 



# %%
def plot_umap(mapper, headline_id:np.array, latent_feature:np.array): 
	height, width = 400, 500 

	# Get the topic label. 
	latent_topic = np.argmax(latent_feature, axis=1) 
	hover_topics = pd.DataFrame(data={"headline_id": headline_id, "topic": latent_topic}) 

	# Plot. 
	umap.plot.output_notebook() 
	plot_umap = umap.plot.interactive(
		mapper, labels=latent_topic, hover_data=hover_topics, point_size=5, height=height, width=width
	) 
	umap.plot.show(plot_umap) 



# %%
def plot_correlation(data, x:str, y:str, xlim:tuple=(0,4), ylim:tuple=(0,4), format_text:str=".2f"): 
    height, width = 300, 400
    chart_title = "Correlation Between (True) & (Pred)" 

    # Base encoding. 
    chart = alt.Chart(data) \
        .mark_point(opacity=1) \
        .encode(
            x=alt.X(
                f"{x}:Q", 
                axis=alt.Axis(title=x, titleFontSize=14, labelFontSize=10, labelAngle=0), 
				scale=alt.Scale(domain=xlim), 
            ),
            y=alt.Y(
                f"{y}:Q", 
                axis=alt.Axis(title=y, titleFontSize=14, labelFontSize=10), 
				scale=alt.Scale(domain=ylim), 
            ), 
            tooltip=[
                alt.Tooltip(f"{x}:Q", title=x, format=format_text), 
                alt.Tooltip(f"{y}:Q", title=y, format=format_text), 
            ], 
        ) \
        .properties(title=chart_title, height=height, width=width) 

    chart += chart.transform_regression(x, y).mark_line(color="red") 
    return chart.interactive() 



# %% 
def plot_discre_dist(data, x:str, format_text:str=".2f"): 
	height, width = 50, 300 
	chart_title = x.replace("_", " ") 

	# Base encoding. 
	chart = alt.Chart(data[x].value_counts(normalize=True).reset_index(drop=False)) \
		.mark_bar(size=50) \
		.encode(
			x=alt.X(
				f"sum({x}):Q", 
				axis=alt.Axis(title="", titleFontSize=14, labelFontSize=10, labelAngle=0), 
				scale=alt.Scale(domain=[0,1]), 
			),
			color=alt.Color(
				f"index:N", 
				scale=alt.Scale(scheme="blues", reverse=False),
                legend=alt.Legend(title="Label categories", direction="vertical"), 
			), 
			tooltip=[
				alt.Tooltip(f"{x}:Q", title=x, format=format_text), 
				alt.Tooltip(f"index:N", title="categories"), 
			], 
		) \
		.properties(title=chart_title, height=height, width=width) 

	return chart 



# %% 
def plot_multiverse_analysis(data, x:str, y:str, err_minmax:tuple, format_text:str=".3f"): 
	height, width = 400, 800 
	chart_title = "Multiverse Analysis Result (95% confidence interval)" 
	sort_experiment = data[y].to_list() 

	# Base encoding. 
	base = alt.Chart(data) \
		.encode(
			x=alt.X(
				f"{x}:Q", 
				axis=alt.Axis(title=x, titleFontSize=14, labelFontSize=10, labelAngle=0), 
			),
			y=alt.Y(
				f"{y}:N", 
				axis=alt.Axis(title=y, titleFontSize=14, labelFontSize=10, labelAngle=0), 
				sort=sort_experiment, 
			),
		) \
		.properties(title=chart_title, height=height, width=width) 

	chart = base \
		.mark_point(size=100, filled=True, color="black") \
		.encode(
			tooltip=[
				alt.Tooltip(f"{x}:Q", title=x, format=format_text), 
				alt.Tooltip(f"{y}:N", title="component"), 
			], 
		)

	errorbars = base \
		.mark_errorbar() \
		.encode(
			x=alt.X(f"{err_minmax[0]}:Q", title=""), 
			y=alt.Y(f"{y}:N", sort=sort_experiment), 
			x2=alt.X2(f"{err_minmax[1]}:Q", title=""), 
		) 

	return (chart + errorbars).interactive() 
