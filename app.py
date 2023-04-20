from dash import Dash, dcc, html, Input, Output, no_update
import plotly.express as px
import geotable
import re


def df_clean(df):
    # drop unused columns
    df = df.drop(columns=['geometry_layer', 'geometry_proj4'])

    # find img link
    df['img'] = df['Description']\
        .apply(lambda x: re.findall('<img src="(.*)" height', x)[0])\
        .str.strip()

    # find member name
    df['member'] = df['Description']\
        .apply(lambda x: re.findall('メンバー／(.*)<br>住', x)[0])\
        .str.strip()

    # find address
    df['address'] = df['Description']\
        .apply(lambda x: re.findall('住所／(.*)<br>営', x)[0])\
        .str.strip()

    # split hours & holidays
    df[['hours', 'holidays']] = df['Description']\
        .apply(lambda x: re.findall('営業時間／(.*)', x)[0])\
        .str.split('定休日／', expand=True)

    # clean hours
    df['hours'] = df['hours']\
        .apply(lambda x: x.rstrip('<br>').strip())\
        .str.replace('\u3000', '')\
        .str.replace('：', ':')\
        .str.replace('~', '～').str.replace(' ～ ', '～')\
        .str.replace('<br>', ' ')
    # df[['hours_wkdy', 'hours_wknd']] = df['hours'].str.split('<br>', expand=True).iloc[:,:2]

    # clean holidays
    df['holidays'] = df['holidays']\
        .fillna('なし')\
        .str.split('<br>', expand=True)\
        .iloc[:,0]

    # remove Description
    df = df.drop(columns=['Description'])

    return df


t = geotable.load("data/machiaruki.kml")
t_clean = df_clean(t)


fig = px.scatter_mapbox(
    t_clean,
    lat=t_clean.geometry_object.apply(lambda x: x.y),
    lon=t_clean.geometry_object.apply(lambda x: x.x),
    # custom_data=['Name', 'member', 'address', 'hours'],
    opacity=0.7,
    zoom=10,
    height=700,
    mapbox_style='open-street-map'
    )

# turn off native plotly.js hover effects - make sure to use
# hoverinfo="none" rather than "skip" which also halts events.
fig.update_traces(hoverinfo="none", hovertemplate=None)



app = Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id="graph-basic-2", figure=fig, clear_on_unhover=True),
    dcc.Tooltip(id="graph-tooltip"),
])


@app.callback(
    Output("graph-tooltip", "show"),
    Output("graph-tooltip", "bbox"),
    Output("graph-tooltip", "children"),
    Input("graph-basic-2", "hoverData"),
)


def display_hover(hoverData):
    if hoverData is None:
        return False, no_update, no_update

    # demo only shows the first point, but other points may also be available
    pt = hoverData["points"][0]
    bbox = pt["bbox"]
    num = pt["pointNumber"]

    t_row = t_clean.iloc[num]
    img_src = t_row['img']
    name = t_row['Name']
    member = t_row['member']
    address = t_row['address']
    hours = t_row['hours']
    holidays = t_row['holidays']

    children = [
        html.Div([
            html.Img(src=img_src, style={"width": "100%"}),
            html.P(f'{member}'),
            html.H3(f'{name}', style={"color": "darkblue", "overflow-wrap": "break-word"}),
            html.P(f'{address}'),
            html.P(f'営業時間：{hours}'),
            html.P(f'定休日：{holidays}')
        ], style={'width': '300px', 'white-space': 'normal'})
    ]

    return True, bbox, children


if __name__ == "__main__":
    app.run_server(debug=True)
