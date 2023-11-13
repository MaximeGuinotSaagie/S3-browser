import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import boto3
from botocore.exceptions import NoCredentialsError

# Initialize Dash app
app = dash.Dash(__name__)

# AWS S3 credentials
AWS_ACCESS_KEY = 'your_access_key'
AWS_SECRET_KEY = 'your_secret_key'
BUCKET_NAME = 'your_bucket_name'

# Connect to S3
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

# Dash layout
app.layout = html.Div([
    html.H1("S3 Browser"),
    dcc.Input(id='path-input', type='text', value='', placeholder='Enter folder path'),
    html.Button('Submit', id='submit-button'),
    dcc.Loading(
        id="loading",
        type="default",
        children=[
            dcc.Graph(id='file-list'),
        ],
    ),
])


# Callback to update file list based on input path
@app.callback(
    Output('file-list', 'figure'),
    [Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('path-input', 'value')]
)
def update_file_list(n_clicks, path):
    try:
        # List objects in the specified path
        objects = s3.list_objects(Bucket=BUCKET_NAME, Prefix=path)['Contents']
        files = [obj['Key'] for obj in objects]

        # Create a bar chart with file names
        fig = {
            'data': [{'x': files, 'type': 'bar', 'name': 'File List'}],
            'layout': {'title': f'Files in {path}', 'xaxis': {'title': 'File Name'}, 'yaxis': {'title': 'Count'}}
        }
    except NoCredentialsError:
        return "Credentials not available."

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
