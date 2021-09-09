# COMS4111 SP2021 Project 1.3

PostgreSQL account: hg2579

URL: http://35.201.242.180:8080/

Features from proposal:

SQL query dynamic generating:

- Table selection: a user can select one or more tables to display. Note that we encode some constraints, when selecting multiple tables, for example, if a vehicle is not selected then the driver cannot be selected (weak entity).

- Keyword search: the user can specify a column and search for keyword in that column. For example, getting all drivers named Albert.

- Sorting: query results can be sorted by user selected column, in either ascending or descending order.


- Interactive maps that show the pickups and dropoffs distribution over different taxi zones. 

- Data modification tools: a user can insert, update and delete records into tables.

- FHV Bases statistics: a user can view the statistics such as trip count, number of vehicles and number of drivers registered under the given base. A user can also sort and restrict the number of rows per page.

Additional features:

- Paging: due to the large amount of data we have, we develop a paging mechanism to fetch 10 or 25 or 100 records each time, but the user can jump to next pages to view more data.

Not implemented features:

- Displaying the distribution of FHV trips on time. Reason: there is no "time slot" information in the NYC OpenData website and we only have the "dates". Additionally,  the data of FHV trips is too large, we used the first 100k rows, which cover only two days so it is not useful to see the distribution over 2 days.

Interesting pages:

The “View Data” page. 

1. Weak entity constraint: We allow the user to select a list of tables they want to view at the same time. The underlying operation is join. However, we want to restrict not useful joining operations. For example, “taxi_zones” is a weak entity of “trips”. When the user doesn't select “trips”, we will disable the checkbox for “taxi_zones”. When the selected number of tables is just 1, of course we allow the user to view the “taxi_zones” table on its own.
2. Paging: We use the OFFSET keyword provided by the PostgreSQL database to perform paging. The user can pick the number of rows per page in the webpage, then we  will run SQL query to obtain the total number of records, then the total number of pages is calculated by (1+(total number of records)/(rows per page)). Then the corresponding SQL is limit x offset y, where x=row per page, y = row per page * (current page number - 1). In this way, the user can view a batch of data at a time. Instead of loading all of the records at once, which may cause performance problems.
3. Search: We use the ILIKE keyword provided by the PostgreSQL database for case-insensitive pattern matching in keyword search. We also use the percent sign (%) to match any sequence of zero or more characters. Therefore the SQL generated would be “WHERE column_name ILIKE %keyword%”.

The interactive map.

A map is generated from a geojson file we downloaded from NYC OpenData website. The file contains coordinates and shapes of each zone. We then modified this file by adding the information about the number of pickups and dropoffs by querying the database for count of pickups and dropoffs of each zone. For the visualization of the geojson map, we used the mapbox.com platform. We configured the map to give each zone different color based on the number of pickups/dropoffs and to display trip number for each zone.

The map visualizes the trips data from the database, which allows us to see the trips distribution among all NYC zones.
