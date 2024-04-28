import boto3
import requests
from datetime import datetime

# This is dumb
# But for some reason this lambda function decides to cache the results of the previous run
# meaning it doesn't show the correct output when students change something.
# How big is the cache ? Does it have a TTL ? Who knows, thanks AWS
def reset_lambda_function_cache(function_name):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    lambda_client = boto3.client('lambda')
    lambda_client.update_function_configuration(
        FunctionName=function_name,
        Description=current_time
    )

reset_lambda_function_cache("test-lab3")

s3 = boto3.Session().client('s3')
lab = "lab3"

def already_passed(uniid):
    try:
        s3.head_object(Bucket='ica0017-results', Key=f'{lab}/{uniid}/')
        print(f'Congrats {uniid}, you have already passed {lab}')
        return True
    except:
        return False
    
def confirm_files_exist(bucket_name):
    try:
        s3.head_object(Bucket=bucket_name, Key='index.html')
        s3.head_object(Bucket=bucket_name, Key='error.html')
    except:
        raise Exception(f"Either the index.html or error.html file is missing from your bucket")

def check_file_matches_content(bucket_name, file, content):
    #website_url = f"http://{bucket_name}.s3-website-{s3.meta.region_name}.amazonaws.com/"
    website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com/{file}"

    try:
        response = requests.get(website_url)
        website_content = response.text
    except:
        raise Exception(f"\nThe file {file} is not accessible thourght this url \n{website_url}\nCheck the object permissions.")
    
    if content in website_content:
        print(f"The file {file} has the correct content {website_content}")
    else:
        raise Exception(f"The website has the wrong content.\n Was expecting {content}\n but got this instead {website_content}")

def pass_student(uniid):
    try:
        s3.put_object(Bucket='ica0017-results', Key=f"{lab}/{uniid}/")
        print(f"{uniid} folder created in the ica0017-results bucket")
        print(f"Congratiulations {uniid}, you have passed {lab}")
    except Exception as e:
        raise Exception(f"Error creating {uniid} folder in the ica0017-results bucket: {e}\nContact the teacher")

def lambda_handler(event, context):
    if 'Uniid' not in event:
        raise Exception(f"Event does not contain 'Uniid'.\n The event provided by you is \n{event}\n")

    uniid = event['Uniid']
    bucket_name = f"ica0017-{uniid}"

    if not already_passed(uniid):
        confirm_files_exist(bucket_name)

        files_and_expected_content = {
            'index.html': uniid,
            'error.html': ""
        }
        for file, content in files_and_expected_content.items():
            check_file_matches_content(bucket_name, file, content)
        pass_student(uniid)
        
#lambda_handler({"Uniid": "lars"}, "test")
