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
    app.run(host='0.0.0.0', debug=True)
