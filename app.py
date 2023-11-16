import os
import dash
from dash import dcc, html, Input as DashInput, Output as DashOutput
from dash.dependencies import Input, Output, State
import boto3
from botocore.exceptions import NoCredentialsError
import base64
import io
from dash_bootstrap_components import themes

app = dash.Dash(__name__, external_stylesheets=[themes.BOOTSTRAP])

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["AWS_S3_ENDPOINT"],
    region_name=os.environ["AWS_REGION_NAME"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
)

app.layout = html.Div([
    html.H1("S3 Browser"),
    dcc.Dropdown(
        id='bucket-dropdown',
        options=[],
        multi=False,
        value='',
        placeholder='Select a bucket'
    ),
    dcc.Loading(
        id="loading",
        type="default",
        children=[
            html.Div(id='file-list'),
            dcc.Upload(
                id='upload-data',
                children=html.Button('Upload File'),
                multiple=False
            ),
        ],
    ),
    # Add the page-load-trigger button and hide it with style
    html.Button(id='page-load-trigger', style={'display': 'none'})
])

@app.callback(
    Output('bucket-dropdown', 'options'),
    [Input('bucket-dropdown', 'search_value'),
     Input('page-load-trigger', 'n_clicks')],
    prevent_initial_call=True
)
def update_bucket_options(search_value, n_clicks):
    try:
        buckets = s3.list_buckets()['Buckets']
        options = [{'label': bucket['Name'], 'value': bucket['Name']} for bucket in buckets]
    except NoCredentialsError:
        return []

    return options
    
def update_file_list(selected_bucket, contents):
    try:
        if not selected_bucket:
            return []

        objects = s3.list_objects(Bucket=selected_bucket)['Contents']
        file_info = []

        for obj in objects:
            if obj['Size'] == 0:
                continue

            file_path = obj['Key']
            file_size = format_file_size(obj['Size'])
            icon = '📂' if file_path.endswith('/') else '📄'

            file_info.append(html.Div([
                html.Div(icon, style={'marginRight': '5px', 'display': 'inline-block', 'vertical-align': 'middle'}),
                html.Div(f"{file_path}, Size: {file_size}", className='file-box', style={'display': 'inline-block', 'vertical-align': 'middle'}),
                html.A("Download", href=f"/download/{selected_bucket}/{file_path}", className="download-link", download=file_path)
            ], className='file-entry'))

        if contents is not None:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            original_filename = dash.callback_context.inputs[1]['filename']
            file_path = original_filename
            s3.upload_fileobj(io.BytesIO(decoded), selected_bucket, file_path)

    except NoCredentialsError:
        return []

    return file_info

@app.server.route("/download/<bucket>/<file_path>")
def download_file(bucket, file_path):
    try:
        file_content = s3.get_object(Bucket=bucket, Key=file_path)['Body'].read()
        response = dash.send_file({
            'content': file_content,
            'filename': file_path,
            'mimetype': 'application/octet-stream'
        })

        return response

    except NoCredentialsError:
        return "Credentials not available."

def format_file_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return "{:.2f} {}".format(size, unit)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
