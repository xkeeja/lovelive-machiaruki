from dash import Dash, dcc, html, Input, Output, no_update
import plotly.express as px
import geotable
import geocoder
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
        .str.replace('<br>', ' ')\
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
    opacity=0.7,
    zoom=10,
    height=700,
    mapbox_style='open-street-map'
    )


g = geocoder.ip('me')
fig.add_scattermapbox(
    lat=[g.latlng[0]],
    lon=[g.latlng[1]],
    showlegend=False,
    marker={'size': 12},
    opacity=0.8
)


fig.update_traces(marker=dict(size=12),
                  selector=dict(mode='markers'))

# turn off native plotly.js hover effects - make sure to use
# hoverinfo="none" rather than "skip" which also halts events.
fig.update_traces(hoverinfo="none", hovertemplate=None)



app = Dash(__name__)

app.layout = html.Div([
    html.H1('沼津 まちあるき スタンプ 設置店舗', style={'text-align': 'center'}),
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

    # don't show hover data for current location marker
    if [pt['lat'], pt['lon']] == g.latlng:
        return False, no_update, no_update

    t_row = t_clean.iloc[num]
    img_src = t_row['img']
    name = t_row['Name']

    member = t_row['member']
    member_colors = {
        '高海千歌': '#F0A20B',
        '桜内梨子': '#E9A9E8',
        '松浦果南': '#13E8AE',
        '黒澤ダイヤ': '#F23B4C',
        '渡辺曜': '#49B9F9',
        '津島善子': '#898989',
        '国木田花丸': '#E6D617',
        '小原鞠莉': '#AE58EB',
        '黒澤ルビィ': '#FB75E4'
    }

    address = t_row['address']
    address_r = [html.B('[住所]'), html.Br()]
    for i in address.split():
        address_r.append(i)
        address_r.append(html.Br())

    hours = t_row['hours']
    hours_r = [html.B('[営業時間]'), html.Br()]
    for i in hours.split():
        hours_r.append(i)
        hours_r.append(html.Br())

    holidays = t_row['holidays']
    holidays_r = [html.B('[定休日]'), html.Br()]
    for i in holidays.split():
        holidays_r.append(i)
        holidays_r.append(html.Br())

    children = [
        html.Div([
            html.Img(src=img_src, style={"width": "100%"}),
            html.P(member, style={"color": member_colors[member]}),
            html.H3(html.B(name), style={"color": "darkblue", "overflow-wrap": "break-word"}),
            html.P(address_r),
            html.P(hours_r),
            html.P(holidays_r)
        ], style={'width': '300px', 'white-space': 'normal'})
    ]

    return True, bbox, children


if __name__ == "__main__":
    app.run_server(debug=True)
