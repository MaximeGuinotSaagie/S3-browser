import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import boto3
from botocore.exceptions import NoCredentialsError
from dash_bootstrap_components import themes

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[themes.BOOTSTRAP])

# AWS S3 credentials
s3_access_key = os.environ["AWS_ACCESS_KEY_ID"]
s3_secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
s3_bucket_name = 'template-projects'

s3 = boto3.client("s3",
                  endpoint_url=os.environ["AWS_S3_ENDPOINT"],
                  region_name=os.environ["AWS_REGION_NAME"],
                  aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                  aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"])

# Function to format file sizes
def format_file_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return "{:.2f} {}".format(size, unit)

# Dash layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # Add Location component
    html.H1("S3 Browser"),
    html.Button('Drill Up', id='drill-up-button', n_clicks=0),
    dcc.Loading(
        id="loading",
        type="default",
        children=[
            html.Div(id='file-list'),
        ],
    ),
])


# Callback to update file list based on input path
@app.callback(
    [Output('file-list', 'children'),
     Output('drill-up-button', 'style')],
    [Input('url', 'pathname'),
     Input('drill-up-button', 'n_clicks')],
    prevent_initial_call=True
)
def update_file_list(pathname, n_clicks):
    try:
        # Extract the folder path from the URL
        path = pathname.split("/path/")[-1] if "/path/" in pathname else ""

        # If the path is empty, set it to the root level
        path = path or ""

        # Check if the button was clicked for drill-up
        drill_up_style = {'display': 'none'}
        if n_clicks > 0:
            # Drill up by removing the last folder from the path
            path_list = path.split('/')
            if len(path_list) > 1:
                path = '/'.join(path_list[:-1])
            else:
                # If already at root, set path to empty to display root files
                path = ""

        # List objects in the specified path
        objects = s3.list_objects(Bucket=s3_bucket_name, Prefix=path)['Contents']

        # Create a list of file information as text and clickable links
        file_info = []
        for obj in objects:
            file_path = obj['Key']
            # Display only files of the first folder level
            if path and '/' in file_path[len(path):]:
                continue
            file_size = format_file_size(obj['Size'])
            # Check if the object is a folder or file
            icon = '📂' if file_path.endswith('/') else '📄'
            file_info.append(html.Div([
                html.Span(icon, style={'marginRight': '5px'}),
                dcc.Link(f"{file_path}, Size: {file_size}", href=f'/path/{file_path}')
            ], className='file-entry'))

        # Display the drill-up button only if the current path is not the root
        if path:
            drill_up_style = {'display': 'inline-block'}

    except NoCredentialsError:
        return "Credentials not available.", {'display': 'none'}

    return file_info, drill_up_style


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
