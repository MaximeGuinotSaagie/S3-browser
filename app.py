import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import boto3
from botocore.exceptions import NoCredentialsError

# Initialize Dash app
app = dash.Dash(__name__)

# AWS S3 credentials
s3_access_key = os.environ["AWS_ACCESS_KEY_ID"]
s3_secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
s3_bucket_name = 'template-projects'

s3 = boto3.client("s3",
                  endpoint_url=os.environ["AWS_S3_ENDPOINT"],
                  region_name=os.environ["AWS_REGION_NAME"],
                  aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                  aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"])

# Dash layout
app.layout = html.Div([
    html.H1("S3 Browser"),
    dcc.Input(id='path-input', type='text', value='', placeholder='Enter folder path'),
    html.Button('Submit', id='submit-button'),
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
    Output('file-list', 'children'),
    [Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('path-input', 'value')]
)
def update_file_list(n_clicks, path):
    try:
        # List objects in the specified path
        objects = s3.list_objects(Bucket=s3_bucket_name, Prefix=path)['Contents']

        # Create a list of file information as text and clickable links
        file_info = []
        for obj in objects:
            file_path = obj['Key']
            file_size = obj['Size']
            file_info.append(html.Div([
                dcc.Link(f"File: {file_path}, Size: {file_size} bytes", href=f'/path/{file_path}')
            ]))

    except NoCredentialsError:
        return "Credentials not available."

    return file_info


# Callback to handle drill-through links
@app.callback(
    Output('path-input', 'value'),
    [Input('file-list', 'children')],
    prevent_initial_call=True
)
def update_path_on_link_click(children):
    # Get the path from the clicked link
    clicked_link = [child for child in children if isinstance(child, html.Div) and 'dcc-link' in child.props['children'][0].props['className']]

    if clicked_link:
        path = clicked_link[0].props['children'][0].props['children'].split(": ")[1].split(",")[0]
        return path
    else:
        raise dash.exceptions.PreventUpdate


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
