# OCP-Reform
Overlay transit, grocery and distance to parks, services to show a more modern, health-oriented understanding of where homes should be located. And then hand that to council.

A sample of what we have so far: https://homesforliving.github.io/OCP-Reform/

![image](https://user-images.githubusercontent.com/36494032/233565452-6071d5dc-d47c-4591-bcf5-443b80ed543f.png)

## Project Structure
You'll first need to download the CRD Properties dataset: [here](https://hub.arcgis.com/datasets/SIPP::crd-properties/explore?layer=3&location=48.440229%2C-123.278142%2C13.00) and put it in the `CRD Properties` folder. Everything else (zoning, roads, etc.) is already here in Github.

The various Python scripts are as follows, in the order you should run them for the first time:
- `osm_analyzer.py` defines an OSM query and collects csv files of various amenities that are saved in the `amenities` folder
- `property_data_collection.py` simplifies the CRD Properties dataset to specific municipalities, removes certain properties from the dataset (e.g. Beacon Hill Park), and dissolves different geometries that have the same street address.
- `OCP_score_generation.py` contains functions that:
  - Use the amenity csv files collected by `osm_analyzer.py`, as well as a function in - `transit_score.py`, to generate amenity and transit scores to each property.
  - Aggregate the scores together using various weights defined in `amenity weights.csv` to create a final 'OCP Score'
- `mapping.py` does everything else: it uses our existing zoning map to apply current zoning to properties, and uses different rules to create new, proposed zoning     for each property, and creates the maps for plotly

Finally, the `docs` folder contains the html/css/js for the website. Not that this is just for internal discussion - our current plan is to post this on the official hfl website.

## I want to run this myself
From scratch, what you'll need to do is:
- Download the CRD Properties dataset above
- Run `simplify_properties()` in `property_data_collection.py`
- Run `osm_analyzer.py`
- Run `create_property_scores()` in `OCP_score_generation.py`
- Run `mapping.py`, where you can change the maps, proposed zoning, etc.

In reality, the outputs of the first 4 bullets are already stored here in Github. So if you're only interested in tweaking the mapping, just run `mapping.py`.

## Data sources
CRD Properties: https://hub.arcgis.com/datasets/SIPP::crd-properties/explore?layer=3&location=48.440229%2C-123.278142%2C13.00

Major roads: https://hub.arcgis.com/datasets/SIPP::crd-roads/explore?layer=10&location=48.450182%2C-123.318805%2C12.86

Highways: https://hub.arcgis.com/datasets/SIPP::crd-roads/explore?layer=7&location=48.617731%2C-123.762900%2C12.86

Zoning: https://github.com/homesforliving/mapping